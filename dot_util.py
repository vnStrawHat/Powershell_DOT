import re
import os
import uuid
import subprocess
import logging


DEBUG = False


def setDebug(value):
    global DEBUG
    if value:
        DEBUG = True
    else:
        DEBUG = False


def initLogger():
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


def getLenAndIter(iterator):
    temp = list(iterator)
    return len(temp), iter(temp)


def remove_ticks(string):
    string = string.replace('`', '')
    return string


def remove_caret(string):
    string = string.replace("^", "")
    return string


def remove_char(string):
    for value in re.findall("(\[[Cc][Hh][Aa][Rr]\])([0-9]{1,3})", string):
        string = string.replace(value, '"%s"' % chr(int(value.split("]")[1])))
    return string


def remove_space(string):
    return string.replace("  ", " ")


def remove_null_char(string):
    return string.replace("\x00", "")


def remove_quote_escape(string):
    return string.replace("\\'", "'").replace('\\"', '"')


def string_plus(string):
    string_plus_reg = r'(\()(\s*)([\'\"][\w\s\+\"\-\'\:]+[\'\"])(\s*)(\))'
    s_len, string_plus_matches = getLenAndIter(re.finditer(string_plus_reg, string, flags=re.IGNORECASE | re.MULTILINE))
    if s_len > 0:
        logging.info(" [#] Found %s \"String Plus tactics\". Try to De-Obfuscate..." % str(s_len))
        logging.info("    [+] Try to De-Obfuscate...")
        for match in string_plus_matches:
            obfus_iex = match.group()
            deobfuscate_block = PS_Execute_Script_Block(obfus_iex, out_file=False)
            if deobfuscate_block is not None:
                logging.debug("  -> Replace %s by %s" % (obfus_iex, deobfuscate_block))
                string = string.replace(obfus_iex, deobfuscate_block)

        logging.info("    [+] De-Obfuscate successful")
        return string
    else:
        logging.info(" [#] Do not found any \"String Plus tactics\" in your script")

    return string


def remove_string_by_assign(string):
    match_reg = r'(\[[sS][tT][rR][iI][nN][gG]\])(\[[Cc][Hh][Aa][Rr]\])([0-9]{1,3})'
    matches = re.findall(match_reg, string, flags=re.IGNORECASE | re.MULTILINE)
    logging.info(" [#] Found %s [String][Char]xxx tactics" % str(len(matches)))
    for match in matches:
        logging.info("    [+] Try to De-Obfuscate...")
        replace_str = match[0] + match[1] + match[2]
        logging.info("    [+] Replace %s...[snip]... by %s" % (replace_str[:20], "'" + match[2] + "'"))
        string = string.replace(replace_str, "'" + match[2] + "'")
    return string


def remove_format_string(string):
    splat_reg = r"(\(\s*[\'\"])({\d+})+[`\"]\s*-[fF]\s*([\'\"][^[\'\"\]]*[\'\"],?)+(\s*\))"
    f_len, format_string_matches = getLenAndIter(re.finditer(splat_reg, string, flags=re.IGNORECASE | re.MULTILINE))
    if f_len > 0:
        logging.info(" [#] Found %s \"Format String Operator tactics\"" % str(f_len))
        logging.info("    [+] Try to De-Obfuscate...")
        for match in format_string_matches:
            block = match.group()
            block_deobfuscated = PS_Execute_Script_Block(block)
            if block_deobfuscated is not None:
                logging.info("      -> Replace %s...[snip]... by %s" % (block[:20], block_deobfuscated[:20]))
                string = string.replace(block, block_deobfuscated)
            else:
                logging.debug("     -> Deobfuscate Script Block Failed")
                pass

        logging.info("    [+] De-Obfuscate successful")
        return string
    else:
        logging.info(" [#] Do not found any \"Format String Operator tactics\" in your script")

    return string


def iex_behind_pipeline(string):
    string = re.sub(r"^\s", "", string)
    clean_iex_reg = r'(\|\s*)(iex|invoke-expression)'
    obfus_iex_reg = r'(\|\s*)(|[\.\&]\s*)(\()(.*)(\))'

    c_len, clean_iex_matches = getLenAndIter(re.finditer(clean_iex_reg, string, flags=re.IGNORECASE | re.MULTILINE))
    o_len, obfus_iex_matches = getLenAndIter(re.finditer(obfus_iex_reg, string, flags=re.IGNORECASE | re.MULTILINE))
    if c_len > 0:
        for match in clean_iex_matches:
            logging.info(" [#] Found %s \"Pipeline IEX tactics\". Try to De-Obfuscate..." % str(c_len))
            clean_iex = match.group()
            logging.info("    [+] Verify IEX")
            logging.debug("     -> De-Obfuscate %s" % clean_iex)
            if verify_iex(clean_iex):
                logging.info("    [+] Try to De-Obfuscate...")
                logging.debug("     -> Replace %s...[snip]... by %s" % (clean_iex[:20], ""))
                string = string.replace(clean_iex, "")
                deobfuscate_string = PS_Execute_Script_Block(string)
                if deobfuscate_string is not None:
                    logging.info("    [+] De-Obfuscate successful")
                    return deobfuscate_string
            else:
                logging.info("    [+] Do nothing")
    else:
        logging.info(" [#] Do not found any \"Pipeline IEX tactics\" in your script")

    if o_len > 0:
        for match in obfus_iex_matches:
            logging.info(" Found %s \"Pipeline IEX (Obfuscated) tactics\". Try to De-Obfuscate..." % str(o_len))
            obfus_iex = match.group()
            logging.info("    [+] Verify IEX")
            logging.debug("     -> Replace %s...[snip]... by %s" % (obfus_iex[:20], ""))
            logging.debug("     -> Script block: %s" % obfus_iex)
            if verify_iex(obfus_iex):
                logging.info("    [+] Try to De-Obfuscate...")
                string = string.replace(obfus_iex, "")
                deobfuscate_string = PS_Execute_Script_Block(string)
                if deobfuscate_string is not None:
                    logging.info("    [+] De-Obfuscate successful")
                    return deobfuscate_string
            else:
                logging.info("    [+] Do nothing")
    else:
        logging.info(" [#] Do not found any \"Pipeline IEX (Obfuscated) tactics\" in your script")

    return string


def startswith_iex(string):
    string = re.sub(r"^\s", "", string)
    match_reg = r'(^iex|^invoke\-expression)\s*(\()([\w\s\W]+)(\))'
    matches = re.findall(match_reg, string, flags=re.IGNORECASE | re.MULTILINE)
    if len(matches) > 0:
        logging.info(" [#] Found %s \"Starts with IEX tactics\". Try to De-Obfuscate..." % str(len(matches)))
        for match in matches:
            script_block = match[2]
            logging.info("    [+] Try to De-Obfuscate...")
            deobfuscate_string = PS_Execute_Script_Block(script_block)
            if deobfuscate_string is not None:
                logging.info("    [+] De-Obfuscate successful")
                return deobfuscate_string
    else:
        logging.info(" [#] Do not found any \"Starts with IEX tactics\" in your script")

    return string


def semi_colon_iex(string):
    string = re.sub(r"^\s", "", string)
    clean_semi_colon_iex_reg = r'(\;)(\s*)(iex|invoke\-expression)(\s*\()'
    obfus_semi_colon_iex_reg = r'(\;\s*)(&|\.)\s*\((.*?)([\[\]\w\,\+\'\"\-\.\$\)]+)(\))'
    s_len, clean_semi_colon_iex_matches = getLenAndIter(re.finditer(clean_semi_colon_iex_reg, string, flags=re.IGNORECASE | re.MULTILINE))
    o_len, obfus_semi_colon_iex_matches = getLenAndIter(re.finditer(obfus_semi_colon_iex_reg, string, flags=re.IGNORECASE | re.MULTILINE))
    if s_len > 0:
        logging.info(" [#] Found %s \"Semi Colon IEX tactics\". Try to De-Obfuscate..." % str(s_len))
        for match in clean_semi_colon_iex_matches:
            obfus_iex = match.group()
            logging.info("    [+] Try to De-Obfuscate...")
            logging.debug("     -> Replace %s...[snip]... by %s" % (obfus_iex, "; Write-Output ("))
            string = string.replace(obfus_iex, "; Write-Output (")
            deobfuscate_string = PS_Execute_Script_Block(string, out_file=False)
            if deobfuscate_string is not None:
                logging.info("    [+] De-Obfuscate successful")
                return deobfuscate_string
    else:
        logging.info(" [#] Do not found any \"Semi Colon IEX tactics\" in your script")

    if o_len > 0:
        logging.info(" [#] Found %s \"Semi Colon IEX (Obfuscated) tactics\". Try to De-Obfuscate..." % str(o_len))
        for match in obfus_semi_colon_iex_matches:
            obfus_iex = match.group()
            logging.info("    [+] Verify IEX")
            logging.debug("     -> Replace %s...[snip]... by %s" % (obfus_iex, "; Write-Output "))
            if verify_iex(obfus_iex):
                logging.info("    [+] Try to De-Obfuscate...")
                string = string.replace(obfus_iex, "; Write-Output ")
                deobfuscate_string = PS_Execute_Script_Block(string, out_file=False)
                if deobfuscate_string is not None:
                    logging.info("      -> De-Obfuscate successful")
                    return deobfuscate_string
            else:
                logging.info("    [+] Do nothing")
    else:
        logging.info(" [#] Do not found any \"Semi Colon IEX (Obfuscated) tactics\" in your script")

    return string


def startswith_dot_or_and_iex(string):
    string = re.sub(r"^\s", "", string)
    match_reg = r"^(&|\.)\s*\((.*?)([\[\]\w\,\+\'\"\-\.\$\)]+)(\))"
    matches = re.finditer(match_reg, string, flags=re.IGNORECASE | re.MULTILINE)
    d_len, dot_and_iex_matches = getLenAndIter(matches)
    if (d_len > 0):
        logging.info(" [#] Found %s \"&(IEX) or .(IEX) - IEX Obfuscated tactics\". Try to De-Obfuscate..." % str(d_len))
        for match in dot_and_iex_matches:
            obfus_iex = match.group()
            logging.info("    [+] Verify IEX")
            logging.debug("     -> Replace %s...[snip]... by %s" % (obfus_iex[:20], ""))
            if verify_iex(obfus_iex):
                logging.info("    [+] Try to De-Obfuscate...")
                string = string.replace(obfus_iex, "")
                deobfuscate_string = PS_Execute_Script_Block(string)
                if deobfuscate_string is not None:
                    logging.info("    [+] De-Obfuscate successful")
                    return deobfuscate_string
            else:
                logging.info("    [+] Do nothing")
    else:
        logging.info(" [#] Do not found any \"&(IEX) or .(IEX) - IEX Obfuscated tactics\" in your script")

    return string


def verify_iex(script):
    if script.startswith("|"):
        matches = re.findall(r"(\|\s*)(\s*)\(", script, flags=re.IGNORECASE | re.MULTILINE)
        if (len(matches)) == 1:
            temp = ''.join(matches[0])
            logging.debug("     -> Detected pipeline IEX without dot (.). Try to replace...")
            logging.debug("     -> Replace %s...[snip]... by %s" % (temp, "|."))
            script = script.replace(temp, "|.")
    # process &(IEX) or .(IEX) - IEX Obfuscated
    elif (script.startswith(".") or script.startswith("&")):
        logging.debug("     -> Detected &(IEX) or .(IEX) - IEX Obfuscated. Try to replace...")
        logging.debug("     -> Replace %s...[snip]... by %s" % (script, "|" + script))
        script = "|" + script
    elif (script.startswith(";")):
        logging.debug("     -> Detected ; &(IEX) or ; IEX () - IEX Obfuscated. Try to replace...")
        logging.debug("     -> Replace %s...[snip]... by %s" % (script, "|" + script[1:]))
        script = "|" + script[1:]
    else:
        logging.debug("     -> Script Block not start with | or . or & or ;")
        logging.debug("     -> Script Block: %s " % script)
        return False

    try:
        script_block = "\"123456789\"" + script
        exec_output = PS_Execute_Script_Block(script_block, verify_iex=True, out_file=False)
        if exec_output == "123456789":
            script_block_2 = "\"123456789a\"" + script
            exec_output_2 = PS_Execute_Script_Block(script_block_2, verify_iex=True, out_file=False)
            if exec_output_2 == "123456789a":
                logging.debug("     -> Script Block can be execute but seen to be not IEX")
                logging.debug("     -> Script_block: %s" % str(script_block_2))
                return False
            else:
                logging.info("      -> Found IEX")
                return True
        else:
            logging.info("      -> Script Block do not equal IEX")
            return False
    except Exception:
        logging.info("      -> Script block do not equal IEX. Script block failed to execute")
        logging.debug("     -> False to perform verify_iex(). Script Block cannot execute")
        logging.debug("     -> Script Block: %s " % script)
        return False


def PS_Execute_Script_Block(script_block, verify_iex=False, out_file=True):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    fname = str(uuid.uuid1()) + ".tmp"
    script_fname = fname + ".ps1"
    tmp_file = dir_path + os.sep + fname
    temp_script_fname = dir_path + os.sep + script_fname
    try:
        if verify_iex:
            exec_script_block = subprocess.check_output(["powershell.exe", "-c", script_block], timeout=2, stderr=subprocess.STDOUT)
            exec_script_block_output = exec_script_block.decode("utf-8")
            exec_script_block_output = re.sub(r"\s+$", "", exec_script_block_output)
            return(exec_script_block_output)

        if out_file:
            logging.info("      -> Execute script block")
            logging.debug("     -> Out File set to : %s " % str(out_file))
            script_block = re.sub(r"\s+$", "", script_block)
            script_block = script_block + " | Out-File -Encoding ASCII -FilePath \"%s\"" % tmp_file
            temp_script_file = open(temp_script_fname, "w")
            temp_script_file.write(script_block)
            logging.debug("     -> Write temp script file to : %s " % temp_script_fname)
            temp_script_file.close()
            exec_script_block = subprocess.Popen(["powershell.exe", "-F", temp_script_fname], stdout=subprocess.PIPE)
            exec_output = "".join(exec_script_block.stdout)
            exec_output = exec_output.replace("\r", "").replace("\n", "")
            logging.debug("     -> Subprocess exec output: \n")
            logging.debug("     -> %s " % str(exec_output))
            if os.path.isfile(tmp_file):
                logging.debug("     -> Execute script block complete. Output was saved to temp file: %s " % str(tmp_file))
                logging.debug("     -> Read temp file output from : %s " % tmp_file)
                temp_output = open(tmp_file, "r")
                results = temp_output.read()
                temp_output.close()
                results = re.sub(r"\s+$", "", results)
                logging.info("      -> Complete")
                if not DEBUG:
                    os.remove(tmp_file)
                    os.remove(temp_script_fname)
                    logging.debug("     -> Delete temp ouput file: %s " % str(tmp_file))
                    logging.debug("     -> Delete temp script file: %s " % str(temp_script_fname))
                return results
            else:
                logging.info("      -> False to execute PS Script Block. Script cannot execute")
                return ""
        else:
            logging.info("      -> Execute script block")
            logging.debug("     -> Out File set to : %s " % str(out_file))
            script_block = re.sub(r"\s+$", "", script_block)
            temp_script_file = open(temp_script_fname, "w")
            temp_script_file.write(script_block)
            logging.debug("     -> Write temp script file to : %s " % temp_script_fname)
            temp_script_file.close()
            exec_script_block = subprocess.check_output(["powershell.exe", "-c", temp_script_fname], timeout=5)
            exec_script_block_output = exec_script_block.decode("utf-8")
            exec_script_block_output = re.sub(r"\s+$", "", exec_script_block_output)
            logging.debug("     -> Execute script block complete. Output return to STDOUT")
            logging.info("      -> Complete")
            if not DEBUG:
                os.remove(temp_script_fname)
                logging.debug("     -> Delete temp output file: %s " % str(temp_script_fname))

            return(exec_script_block_output)

    except Exception as e:
        logging.debug("     -> Stack Trace: %s" % str(e))
        return None

