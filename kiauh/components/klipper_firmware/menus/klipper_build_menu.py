# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from pathlib import Path
from shutil import copyfile
from typing import List, Set, Type

from components.klipper import KLIPPER_DIR, KLIPPER_KCONFIGS_DIR
from components.klipper_firmware.firmware_utils import (
    run_make,
    run_make_clean,
    run_make_menuconfig,
)
from components.klipper_firmware.flash_options import FlashOptions
from core.logger import DialogType, Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color
from utils.input_utils import get_confirm, get_string_input
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperKConfigMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "固件菜单"
        self.title_color = Color.CYAN
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.flash_options = FlashOptions()
        self.kconfigs_dirname = KLIPPER_KCONFIGS_DIR
        self.kconfig_default = KLIPPER_DIR.joinpath(".config")
        self.configs: List[Path] = []
        self.kconfig = (
            self.kconfig_default if not Path(self.kconfigs_dirname).is_dir() else None
        )

    def run(self) -> None:
        if not self.kconfig:
            super().run()
        else:
            self.flash_options.selected_kconfig = self.kconfig

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        if not Path(self.kconfigs_dirname).is_dir():
            return

        self.input_label_txt = "选择配置或操作以继续 (默认=N)"
        self.default_option = Option(
            method=self.select_config, opt_data=self.kconfig_default
        )

        option_index = 1
        for kconfig in Path(self.kconfigs_dirname).iterdir():
            if not kconfig.name.endswith(".config"):
                continue
            kconfig_path = self.kconfigs_dirname.joinpath(kconfig)
            if Path(kconfig_path).is_file():
                self.configs += [kconfig]
                self.options[str(option_index)] = Option(
                    method=self.select_config, opt_data=kconfig_path
                )
                option_index += 1
        self.options["n"] = Option(
            method=self.select_config, opt_data=self.kconfig_default
        )

    def print_menu(self) -> None:
        cfg_found_str = Color.apply(
            "Previously saved firmware configs found!", Color.GREEN
        )
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {cfg_found_str:^62} ║
            ║                                                       ║
            ║    选择现有配置或创建新配置.                          ║
            ╟───────────────────────────────────────────────────────╢
            ║ 可用固件配置:                                         ║
            """
        )[1:]

        start_index = 1
        for i, s in enumerate(self.configs):
            line = f"{start_index + i}) {s.name}"
            menu += f"║ {line:<54}║\n"

        new_config = Color.apply("N) 创建新的固件配置", Color.GREEN)
        menu += "║                                                       ║\n"
        menu += f"║ {new_config:<62} ║\n"

        menu += "╟───────────────────────────────────────────────────────╢\n"

        print(menu, end="")

    def select_config(self, **kwargs) -> None:
        selection: str | None = kwargs.get("opt_data", None)
        if selection is None:
            raise Exception("opt_data is None")
        if not Path(selection).is_file() and selection != self.kconfig_default:
            raise Exception("opt_data does not exists")
        self.kconfig = selection


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperBuildFirmwareMenu(BaseMenu):
    def __init__(
        self, kconfig: str | None = None, previous_menu: Type[BaseMenu] | None = None
    ):
        super().__init__()
        self.title = "编译菜单"
        self.title_color = Color.CYAN
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.deps: Set[str] = {"build-essential", "dpkg-dev", "make"}
        self.missing_deps: List[str] = check_package_install(self.deps)
        self.flash_options = FlashOptions()
        self.kconfigs_dirname = KLIPPER_KCONFIGS_DIR
        self.kconfig_default = KLIPPER_DIR.joinpath(".config")
        self.kconfig = self.flash_options.selected_kconfig

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        self.input_label_txt = "ENTER键安装依赖项"
        self.default_option = Option(method=self.install_missing_deps)

    def run(self):
        # immediately start the build process if all dependencies are met
        if len(self.missing_deps) == 0:
            self.start_build_process()
        else:
            super().run()

    def print_menu(self) -> None:
        txt = Color.apply("Dependencies are missing!", Color.RED)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {txt:^62} ║
            ╟───────────────────────────────────────────────────────╢
            ║ 需要以下依赖项:                                       ║
            ║                                                       ║
            """
        )[1:]

        for d in self.deps:
            status_ok = Color.apply("*INSTALLED*", Color.GREEN)
            status_missing = Color.apply("*MISSING*", Color.RED)
            status = status_missing if d in self.missing_deps else status_ok
            padding = 40 - len(d) + len(status) + (len(status_ok) - len(status))
            d = Color.apply(f"● {d}", Color.CYAN)
            menu += f"║ {d}{status:>{padding}} ║\n"

        menu += "║                                                       ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"

        print(menu, end="")

    def install_missing_deps(self, **kwargs) -> None:
        try:
            update_system_package_lists(silent=False)
            Logger.print_status("安装系统软件包...")
            install_system_packages(self.missing_deps)
        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("安装依赖项失败!")
        finally:
            # restart this menu
            KlipperBuildFirmwareMenu().run()

    def start_build_process(self, **kwargs) -> None:
        try:
            run_make_clean(self.kconfig)
            run_make_menuconfig(self.kconfig)
            run_make(self.kconfig)

            Logger.print_ok("固件编译成功!")
            Logger.print_ok(f"固件文件在 '{KLIPPER_DIR}/out'!")

            if self.kconfig == self.kconfig_default:
                self.save_firmware_config()

        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("固件编译失败!")

        finally:
            if self.previous_menu is not None:
                self.previous_menu().run()

    def save_firmware_config(self) -> None:
        Logger.print_dialog(
            DialogType.CUSTOM,
            [
                "您可以保存多个MCU的固件配置,"
                " 并在Klipper版本升级后使用它们来更新固件"
            ],
            custom_title="Save firmware config",
        )
        if not get_confirm(
            "是否保存固件配置?", default_choice=False
        ):
            return

        filename = self.kconfig_default
        while True:
            Logger.print_dialog(
                DialogType.CUSTOM,
                [
                    "允许使用的字符: 小写字母 a-z、数字 0-9 和连字符 '-'",
                    "命名必须遵守以下规则:",
                    "\n\n",
                    "● 不能包含特殊字符",
                    "● 开头或结尾不能使用连字符 '-'",
                ],
            )
            input_name = get_string_input(
                "输入新的固件配置名称",
                regex=r"^[a-z0-9]+([a-z0-9-]*[a-z0-9])?$",
            )
            filename = self.kconfigs_dirname.joinpath(f"{input_name}.config")

            if Path(filename).is_file():
                if get_confirm(
                    f"固件配置 {input_name} 已存在，覆盖?",
                    default_choice=False,
                ):
                    break

            if Path(filename).is_dir():
                Logger.print_error(f"路径 {filename} 存在，并且它是一个目录")

            if not Path(filename).exists():
                break

        if not get_confirm(
            f"将固件配置保存到 '{filename}'?", default_choice=True
        ):
            Logger.print_info("已取消保存固件配置 ...")
            return

        if not Path(self.kconfigs_dirname).exists():
            Path(self.kconfigs_dirname).mkdir()

        copyfile(self.kconfig_default, filename)

        Logger.print_ok()
        Logger.print_ok(f"固件配置已成功保存到 {filename}")
