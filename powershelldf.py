import os
import sys
import base64
import binascii
import argparse
from df_util import *
import subprocess


def check_necessary_environment_setting():
    print("[INFO] Check nessesery windows environment setting")
    cmd = 'powershell -inputformat none -outputformat text -NonInteractive -Command "Get-MpPreference | select -ExpandProperty \"DisableRealtimeMonitoring\""'
    check_windows_defender_enable = subprocess.check_output(cmd, timeout=5, stderr=subprocess.STDOUT)
    check_windows_defender_enable = check_windows_defender_enable.decode("utf-8")
    check_windows_defender_enable = re.sub(r"\s+$", "", check_windows_defender_enable)
    if check_windows_defender_enable == "True":
        print("[DEBUG] Windows Defender Realtime Monitor was Disabled")
    else:
        print("[DEBUG] Windows Defender Realtime Monitor was Enabled. Please disable before running")
        sys.exit(0)

    cmd = 'powershell -c "Get-ExecutionPolicy"'
    check_powershell_executepolicy = subprocess.check_output(cmd, timeout=5, stderr=subprocess.STDOUT)
    check_powershell_executepolicy = check_powershell_executepolicy.decode("utf-8")
    check_powershell_executepolicy = re.sub(r"\s+$", "", check_powershell_executepolicy)
    if check_powershell_executepolicy == "Bypass" or check_powershell_executepolicy == "Unrestricted":
        print("[DEBUG] Powershell ExecutePolicy was set to: %s" % check_powershell_executepolicy)
    else:
        print("[DEBUG] Powershell ExecutePolicy must be set to Bypass or Unrestricted before running.")
        sys.exit(0)


def disable_windows_defender_realtime_monitor():
    pass


def set_ps_exec_policy_bypass():
    pass


def deobfuscate_ps_script(input_script, output_file, debug=False):
    if debug:
        setDebug(True)
    else:
        setDebug(False)

    initLogger()

    deobfuscated_string = input_script
    prev_string = ""
    round_id = 1
    while True:
        fname = "out_%s.txt" % str(round_id)
        print("--------------------Round %s-------------------" % round_id)
        prev_string = deobfuscated_string
        deobfuscated_string = iex_behind_pipeline(deobfuscated_string)
        deobfuscated_string = startswith_iex(deobfuscated_string)
        deobfuscated_string = startswith_dot_or_and_iex(deobfuscated_string)
        deobfuscated_string = semi_colon_iex(deobfuscated_string)
        deobfuscated_string = remove_ticks(deobfuscated_string)
        deobfuscated_string = remove_caret(deobfuscated_string)
        deobfuscated_string = remove_quote_escape(deobfuscated_string)
        deobfuscated_string = remove_format_string(deobfuscated_string)
        deobfuscated_string = string_plus(deobfuscated_string)

        deobfuscated_string = deobfuscated_string.replace("\r", "")
        deobfuscated_string = deobfuscated_string.split("\n")

        while("" in deobfuscated_string):
            deobfuscated_string.remove("")

        deobfuscated_string = "\n".join(deobfuscated_string)
        if debug:
            fname = "output_roud_%s.txt" % str(round_id)
            f = open(fname, "w")
            f.write(deobfuscated_string)
            f.close()
        else:
            pass

        round_id += 1

        if (prev_string == deobfuscated_string):
            print("-----------------------------------------------")
            print("[#] Write output file to: %s " % output_file)
            f = open(output_file, "w")
            f.write(deobfuscated_string)
            f.close()
            break

        print("[->] Prev String and deobfuscated String is not equal. Go to the next round")
        print("-----------------------------------------------")


def main():
    parser = argparse.ArgumentParser(description="[#] Powershell Deobfuscate Tool by TrungKFC")
    parser.add_argument('-f', '--file', help='obfuscated powershell script')
    parser.add_argument('-o', '--out-file', help='Path to save deobfuscated powershell script', required=True)
    parser.add_argument('-b64', '--base64', help='powershell One-liner Base64 Encoded string')
    parser.add_argument('-force', '--force-run', help='[Need admin right] Disable Windows Defender realtime monitor and Set Powershell ExecutePolicy to Bypass', action='store_true')
    parser.add_argument('-d', '--debug', help='Enable DEBUG. All temp file will not delete', action='store_true')
    args = parser.parse_args()

    check_necessary_environment_setting()

    if args.force_run:
        disable_windows_defender_realtime_monitor()
        set_ps_exec_policy_bypass()

    if args.file:
        input_file = args.file
        output_file = args.out_file

        if os.path.isfile(input_file):
            f = open(input_file, 'r')
            input_script = f.read()
            if args.debug:
                deobfuscate_ps_script(input_script, output_file, debug=True)
            else:
                deobfuscate_ps_script(input_script, output_file)
            sys.exit(0)
        else:
            print("[ERROR]: Input file was not existed")
            sys.exit(0)

    if args.base64:
        try:
            input_script = base64.decodestring(args.base64)
            if args.debug:
                deobfuscate_ps_script(input_script, output_file, debug=True)
            else:
                deobfuscate_ps_script(input_script, output_file)
            sys.exit(0)
        except binascii.Error:
            print("[ERROR]: Input is not Base64 Encode string")
            sys.exit(0)


if __name__ == '__main__':
    main()
