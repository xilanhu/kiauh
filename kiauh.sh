#!/usr/bin/env bash

#=======================================================================#
# Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>       #
#                                                                       #
# This file is part of KIAUH - Klipper Installation And Update Helper   #
# https://github.com/dw-0/kiauh                                         #
#                                                                       #
# This file may be distributed under the terms of the GNU GPLv3 license #
#=======================================================================#

set -e
clear -x

# make sure we have the correct permissions while running the script
umask 022

### sourcing all additional scripts
KIAUH_SRCDIR="$(dirname -- "$(readlink -f "${BASH_SOURCE[0]}")")"
for script in "${KIAUH_SRCDIR}/scripts/"*.sh; do . "${script}"; done
for script in "${KIAUH_SRCDIR}/scripts/ui/"*.sh; do . "${script}"; done

#===================================================#
#=================== UPDATE KIAUH ==================#
#===================================================#

function update_kiauh() {
  status_msg "Updating KIAUH ..."

  cd "${KIAUH_SRCDIR}"
  git reset --hard && git pull

  ok_msg "Update complete! Please restart KIAUH."
  exit 0
}

#===================================================#
#=================== KIAUH STATUS ==================#
#===================================================#

function kiauh_update_avail() {
	echo "false"
	return
}

function save_startup_version() {
  local launch_version

  echo "${1}"

  sed -i "/^version_to_launch=/d" "${INI_FILE}"
  sed -i '$a'"version_to_launch=${1}" "${INI_FILE}"
}

function kiauh_update_dialog() {
  [[ ! $(kiauh_update_avail) == "true" ]] && return
  top_border
  echo -e "|${green}              New KIAUH update available!              ${white}|"
  hr
  echo -e "|${green}  View Changelog: https://git.io/JnmlX                 ${white}|"
  blank_line
  echo -e "|${yellow}  It is recommended to keep KIAUH up to date. Updates  ${white}|"
  echo -e "|${yellow}  usually contain bugfixes, important changes or new   ${white}|"
  echo -e "|${yellow}  features. Please consider updating!                  ${white}|"
  bottom_border

  local yn
  read -p "${cyan}###### Do you want to update now? (Y/n):${white} " yn
  while true; do
    case "${yn}" in
     Y|y|Yes|yes|"")
       do_action "update_kiauh"
       break;;
     N|n|No|no)
       break;;
     *)
       deny_action "kiauh_update_dialog";;
    esac
  done
}

function launch_kiauh_v5() {
    main_menu
}

function launch_kiauh_v6() {
  local entrypoint

  if ! command -v python3 &>/dev/null || [[ $(python3 -V | cut -d " " -f2 | cut -d "." -f2) -lt 8 ]]; then
    echo "未安装Python 3.8或更高版本!"
    echo "请安装Python 3.8或更高版本，然后重试."
    exit 1
  fi

  entrypoint=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")

  export PYTHONPATH="${entrypoint}"

  clear -x
  python3 "${entrypoint}/kiauh.py"
}

function main() {
  read_kiauh_ini "${FUNCNAME[0]}"

  if [[ ${version_to_launch} -eq 5 ]]; then
    launch_kiauh_v5
  elif [[ ${version_to_launch} -eq 6 ]]; then
    launch_kiauh_v6
  else
    top_border
    echo -e "|            ${green}KIAUH v6.0.0-alpha 1现已推出!${white}                |"
    hr
    echo -e "|         查看更新日志: ${magenta}https://git.io/JnmlX${white}            |"
    blank_line
    echo -e "| KIAUH v6 进行了完完全全的重构.                        |"
    echo -e "| 它基于Python 3.8，并有许多改进.                       |"
    blank_line
    echo -e "| ${yellow}注意：版本6仍处于alpha阶段，因此可能会出现错误!${white}       |"
    echo -e "| ${yellow}然而，您的反馈和错误报告非常重要${white}                      |"
    echo -e "| ${yellow}这将帮助完善最终版本的发布.${white}                           |"
    hr
    echo -e "| 您想试用KIAUH V6吗?                                   |"
    echo -e "| 1) 是的                                               |"
    echo -e "| 2) No                                                 |"
    echo -e "| 3) 是的，并且记住我的选择                             |"
    echo -e "| 4) No, remember my choice for next time               |"
    quit_footer
    while true; do
      read -p "${cyan}###### 执行选项:${white} " -e input
      case "${input}" in
        1)
          launch_kiauh_v6
          break;;
        2)
          launch_kiauh_v5
          break;;
        3)
          save_startup_version 6
          launch_kiauh_v6
          break;;
        4)
          save_startup_version 5
          launch_kiauh_v5
          break;;
        Q|q)
          echo -e "${green}###### 打印愉快! ######${white}"; echo
          exit 0;;
        *)
          error_msg "错误的输入!\n";;
      esac
    done && input=""
  fi
}

check_if_ratos
check_euid
init_logfile
set_globals
kiauh_update_dialog
read_kiauh_ini
init_ini
main
