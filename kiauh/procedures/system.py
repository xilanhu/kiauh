# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from pathlib import Path
from subprocess import PIPE, CalledProcessError, run

from core.logger import DialogType, Logger
from utils.common import check_install_dependencies, get_current_date
from utils.fs_utils import check_file_exist
from utils.input_utils import get_confirm, get_string_input


def change_system_hostname() -> None:
    """
    Procedure to change the system hostname.
    :return:
    """

    Logger.print_dialog(
        DialogType.CUSTOM,
        [
            "修改系统主机名后,"
            "您可以通过以下格式在浏览器中访问已安装的Web界面:",
            "\n\n",
            "http://<hostname>.local",
            "\n\n",
            "示例：如果将主机名设置为'my-printer',可通过访问 'http://my-printer.local'",
            "进入控制界面.",
        ],
        custom_title="修改系统主机名",
    )
    if not get_confirm("您要更改主机名吗?", default_choice=False):
        return

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
    hostname = get_string_input(
        "输入新的主机名",
        regex=r"^[a-z0-9]+([a-z0-9-]*[a-z0-9])?$",
    )
    if not get_confirm(f"确定将主机名更改为 '{hostname}'?", default_choice=False):
        Logger.print_info("已取消更改主机名 ...")
        return

    try:
        Logger.print_status("正在更改主机名 ...")

        Logger.print_status("检查依赖项 ...")
        check_install_dependencies({"avahi-daemon"}, include_global=False)

        # create or backup hosts file
        Logger.print_status("正在备份 hosts 文件 ...")
        hosts_file = Path("/etc/hosts")
        if not check_file_exist(hosts_file, True):
            cmd = ["sudo", "touch", hosts_file.as_posix()]
            run(cmd, stderr=PIPE, check=True)
        else:
            date_time = get_current_date()
            name = f"hosts.{date_time.get('date')}-{date_time.get('time')}.bak"
            hosts_file_backup = Path(f"/etc/{name}")
            cmd = [
                "sudo",
                "cp",
                hosts_file.as_posix(),
                hosts_file_backup.as_posix(),
            ]
            run(cmd, stderr=PIPE, check=True)
        Logger.print_ok()

        # call hostnamectl set-hostname <hostname>
        Logger.print_status(f"正在设置主机名为 '{hostname}' ...")
        cmd = ["sudo", "hostnamectl", "set-hostname", hostname]
        run(cmd, stderr=PIPE, check=True)
        Logger.print_ok()

        # add hostname to hosts file at the end of the file
        Logger.print_status("正在写入 /etc/hosts ...")
        stdin = f"127.0.0.1       {hostname}\n"
        cmd = ["sudo", "tee", "-a", hosts_file.as_posix()]
        run(cmd, input=stdin.encode(), stderr=PIPE, stdout=PIPE, check=True)
        Logger.print_ok()

        Logger.print_ok("新主机名配置成功!")
        Logger.print_ok("请重启系统以使更改生效!\n")

    except CalledProcessError as e:
        Logger.print_error(f"更改主机名过程中发生错误: {e}")
        return
