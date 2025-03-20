# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from typing import List

from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.submodules.simple_config_parser.src.simple_config_parser.simple_config_parser import (
    SimpleConfigParser,
)
from extensions.base_extension import BaseExtension
from utils.common import backup_printer_config_dir, moonraker_exists
from utils.input_utils import get_confirm


# noinspection PyMethodMayBeStatic
class SimplyPrintExtension(BaseExtension):
    def install_extension(self, **kwargs) -> None:
        Logger.print_status("正在安装 SimplyPrint ...")

        if not (mr_instances := moonraker_exists("SimplyPrint 安装程序")):
            return

        Logger.print_dialog(
            DialogType.INFO,
            self._construct_dialog(mr_instances, True),
        )

        if not get_confirm(
            "继续 SimplyPrint 的安装?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("正在退出 SimplyPrint 的安装 ...")
            return

        try:
            self._patch_moonraker_confs(mr_instances, True)

        except Exception as e:
            Logger.print_error(f"安装 SimplyPrint 期间出现错误:\n{e}")

    def remove_extension(self, **kwargs) -> None:
        Logger.print_status("在卸载 SimplyPrint ...")

        if not (mr_instances := moonraker_exists("SimplyPrint 卸载程序")):
            return

        Logger.print_dialog(
            DialogType.INFO,
            self._construct_dialog(mr_instances, False),
        )

        if not get_confirm(
            "您真的要卸载 SimplyPrint 吗?",
            default_choice=True,
            allow_go_back=True,
        ):
            Logger.print_info("退出 SimplyPrint 的卸载 ...")
            return

        try:
            self._patch_moonraker_confs(mr_instances, False)

        except Exception as e:
            Logger.print_error(f"卸载 SimplyPrint 期间出现错:\n{e}")

    def _construct_dialog(
        self, mr_instances: List[Moonraker], is_install: bool
    ) -> List[str]:
        mr_names = [f"● {m.service_file_path.name}" for m in mr_instances]
        _type = "安装" if is_install else "卸载"

        return [
            "发现以下 Moonraker 的服务:",
            *mr_names,
            "\n\n",
            f"将为所有 Moonraker 服务 {_type} SimplyPrint. "
            f"{_type}完成后，所有 Moonraker 服务将重新启动!",
        ]

    def _patch_moonraker_confs(
        self, mr_instances: List[Moonraker], is_install: bool
    ) -> None:
        section = "simplyprint"
        _type, _ft = ("Adding", "to") if is_install else ("Removing", "from")

        patched_files = []
        for moonraker in mr_instances:
            Logger.print_status(
                f"{_type} section 'simplyprint' {_ft} {moonraker.cfg_file} ..."
            )
            scp = SimpleConfigParser()
            scp.read_file(moonraker.cfg_file)

            install_and_has_section = is_install and scp.has_section(section)
            uninstall_and_has_no_section = not is_install and not scp.has_section(
                section
            )

            if install_and_has_section or uninstall_and_has_no_section:
                status = "已存在" if is_install else "不存在"
                Logger.print_info(
                    f"'simplyprint' 配置 {status} ! 跳过 ..."
                )
                continue

            if is_install and not scp.has_section("simplyprint"):
                backup_printer_config_dir()
                scp.add_section(section)
            elif not is_install and scp.has_section("simplyprint"):
                backup_printer_config_dir()
                scp.remove_section(section)
            scp.write_file(moonraker.cfg_file)
            patched_files.append(moonraker.cfg_file)

        if patched_files:
            InstanceManager.restart_all(mr_instances)

        install_state = "成功" if patched_files else "已经"
        Logger.print_dialog(
            DialogType.SUCCESS,
            [f"SimplyPrint {install_state} {'' if is_install else 'un'}!"],
            center_content=True,
        )
