# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import sys
import textwrap
from typing import Callable, Type

from components.crowsnest.crowsnest import get_crowsnest_status
from components.klipper.klipper_utils import get_klipper_status
from components.klipperscreen.klipperscreen import get_klipperscreen_status
from components.log_uploads.menus.log_upload_menu import LogUploadMenu
from components.moonraker.utils.utils import get_moonraker_status
from components.webui_client.client_utils import (
    get_client_status,
    get_current_client_config,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.logger import Logger
from core.menus import FooterType
from core.menus.advanced_menu import AdvancedMenu
from core.menus.backup_menu import BackupMenu
from core.menus.base_menu import BaseMenu, Option
from core.menus.install_menu import InstallMenu
from core.menus.remove_menu import RemoveMenu
from core.menus.settings_menu import SettingsMenu
from core.menus.update_menu import UpdateMenu
from core.types.color import Color
from core.types.component_status import ComponentStatus, StatusMap, StatusText
from extensions.extensions_menu import ExtensionsMenu
from utils.common import get_kiauh_version, trunc_string


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class MainMenu(BaseMenu):
    def __init__(self) -> None:
        super().__init__()

        self.header: bool = True
        self.title = "主页菜单"
        self.title_color = Color.CYAN
        self.footer_type: FooterType = FooterType.QUIT

        self.version = ""
        self.kl_status, self.kl_owner, self.kl_repo = "", "", ""
        self.mr_status, self.mr_owner, self.mr_repo = "", "", ""
        self.ms_status, self.fl_status, self.ks_status = "", "", ""
        self.cn_status, self.cc_status = "", ""
        self._init_status()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        """主菜单没有上级菜单"""
        pass

    def set_options(self) -> None:
        self.options = {
            "0": Option(method=self.log_upload_menu),
            "1": Option(method=self.install_menu),
            "2": Option(method=self.update_menu),
            "3": Option(method=self.remove_menu),
            "4": Option(method=self.advanced_menu),
            "5": Option(method=self.backup_menu),
            "e": Option(method=self.extension_menu),
            "s": Option(method=self.settings_menu),
        }

    def _init_status(self) -> None:
        status_vars = ["kl", "mr", "ms", "fl", "ks", "cn"]
        for var in status_vars:
            setattr(
                self,
                f"{var}_status",
                Color.apply("未安装", Color.RED),
            )

    def _fetch_status(self) -> None:
        self.version = "Kiauh更新已禁用"
        self._get_component_status("kl", get_klipper_status)
        self._get_component_status("mr", get_moonraker_status)
        self._get_component_status("ms", get_client_status, MainsailData())
        self._get_component_status("fl", get_client_status, FluiddData())
        self._get_component_status("ks", get_klipperscreen_status)
        self._get_component_status("cn", get_crowsnest_status)
        self.cc_status = get_current_client_config()

    def _get_component_status(self, name: str, status_fn: Callable, *args) -> None:
        status_data: ComponentStatus = status_fn(*args)
        code: int = status_data.status
        status: StatusText = StatusMap[code]
        owner: str = trunc_string(status_data.owner, 23)
        repo: str = trunc_string(status_data.repo, 23)
        instance_count: int = status_data.instances

        count_txt: str = ""
        if instance_count > 0 and code == 2:
            count_txt = f": {instance_count}"

        setattr(self, f"{name}_status", self._format_by_code(code, status, count_txt))
        setattr(self, f"{name}_owner", Color.apply(owner, Color.CYAN))
        setattr(self, f"{name}_repo", Color.apply(repo, Color.CYAN))

    def _format_by_code(self, code: int, status: str, count: str) -> str:
        color = Color.RED
        if code == 0:
            color = Color.RED
        elif code == 1:
            color = Color.YELLOW
        elif code == 2:
            color = Color.GREEN

        return Color.apply(f"{status}{count}", color)

    def print_menu(self) -> None:
        self._fetch_status()

        footer1 = Color.apply(self.version, Color.CYAN)
        link = Color.apply("By: Xilanhu", Color.MAGENTA)
        footer2 = f"Kiauh加速  {link}"
        pad1 = 32
        pad2 = 26
        menu = textwrap.dedent(
            f"""
            ╟──────────────────┬────────────────────────────────────╢
            ║  0) [日志上传]   │   Klipper: {self.kl_status:<{pad1}} ║
            ║                  │     Owner: {self.kl_owner:<{pad1}} ║
            ║  1) [安装]       │      Repo: {self.kl_repo:<{pad1}} ║
            ║  2) [更新]       ├────────────────────────────────────╢
            ║  3) [卸载]       │ Moonraker: {self.mr_status:<{pad1}} ║
            ║  4) [高级]       │     Owner: {self.mr_owner:<{pad1}} ║
            ║  5) [备份]       │      Repo: {self.mr_repo:<{pad1}} ║
            ║                  ├────────────────────────────────────╢
            ║  S) [设置]       │        Mainsail: {self.ms_status:<{pad2}} ║
            ║                  │          Fluidd: {self.fl_status:<{pad2}} ║
            ║ 社区:            │   Client-Config: {self.cc_status:<{pad2}} ║
            ║  E) [扩展]       │                                    ║
            ║                  │   KlipperScreen: {self.ks_status:<{pad2}} ║
            ║                  │       Crowsnest: {self.cn_status:<{pad2}} ║
            ╟──────────────────┼────────────────────────────────────╢
            ║ {footer1:^20} │ {footer2:^41} ║
            ╟──────────────────┴────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def exit(self, **kwargs) -> None:
        Logger.print_ok("###### 打印愉快!", False)
        sys.exit(0)

    def log_upload_menu(self, **kwargs) -> None:
        LogUploadMenu().run()

    def install_menu(self, **kwargs) -> None:
        InstallMenu(previous_menu=self.__class__).run()

    def update_menu(self, **kwargs) -> None:
        UpdateMenu(previous_menu=self.__class__).run()

    def remove_menu(self, **kwargs) -> None:
        RemoveMenu(previous_menu=self.__class__).run()

    def advanced_menu(self, **kwargs) -> None:
        AdvancedMenu(previous_menu=self.__class__).run()

    def backup_menu(self, **kwargs) -> None:
        BackupMenu(previous_menu=self.__class__).run()

    def settings_menu(self, **kwargs) -> None:
        SettingsMenu(previous_menu=self.__class__).run()

    def extension_menu(self, **kwargs) -> None:
        ExtensionsMenu(previous_menu=self.__class__).run()
