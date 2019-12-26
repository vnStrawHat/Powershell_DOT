
# Powershell_DOT (Powershell De-Obfuscation Tool)

## How to use ?

```shell
python powershelldf.py -h
```

## The Goal ?

Tool này sinh ra để defeat Invoke-Obfuscation :)

## The history ?

> Powershell attack đang hot trend gần đây bên quyết đị bú frame tí.

Trong quá trình thực hiện điều tra một số case APT, mình gặp khá nhiều các trường hợp Attacker sử dụng powershell one-liner để cài backdoor vào máy tính người dùng và máy chủ. Dĩ nhiên đa số các trường hợp đoạn powershell đều bị obfuscated. Cá biệt có những case powershell script bị obfuscated đến 7 lần.

Ban đầu mình viết tool này để giải quyết mấy trường hợp các biệt trên. Nhưng sau khi thử nghiệm trên nhiều mẫu powershell obfuscated khác nhau thì nhận ra: "tool mình viết hoạt động tốt hơn mong đợi :D" nên quyết định thêm một vài tính năng nữa nhìn cho nó xịn xò hơn. Ví dụ ứng dụng Machine Learning vào việc Deobfuscate. Nghe có vẻ vãi nhỉ ? watch till the end (rofl)

Target mình nhắm đến đầu tiên là Invoke-Obfuscation cũng là tool mà đa số các mẫu mình gặp phải sử dụng để obfuscate powershell script.

## How it work ?

Ý tưởng ban đầu thì xuất phát sau khi mình đọc bài viết này:
[https://www.endgame.com/blog/technical-blog/deobfuscating-powershell-putting-toothpaste-back-tube](https://www.endgame.com/blog/technical-blog/deobfuscating-powershell-putting-toothpaste-back-tube)

Nhưng mình không nghĩ phức tạp như họ (ban đầu định làm theo như méo biết machine learning, AI, neural network nên bỏ cuộc).

Sau khi thu thập một cơ số kha khá các mẫu powershell script đã bị obfuscated, test các kiểu với Invoke-Obfuscation, thực hiện phân tích và thống kê thì mình rút ra được các kỹ thuật mà Invoke-Obfuscation sử dụng như sau:

### Format string

Kỹ thuật này đơn giản là cắt 1 string gốc ra thành nhiều string con và khi thực thi thì powershell sẽ tự động cộng các string này lại thành string gốc. Có 02 cách để thực hiện trong powershell.

**Cách 1: sử dụng Format String**
Trong powershell có operator là -f để cho phép lập trình viên thực hiên định dạng một string (Đọc thêm ở đây [https://ss64.com/ps/syntax-f-operator.html](https://ss64.com/ps/syntax-f-operator.html)).
Ví dụ:

```powershell
String gốc: Invoke-Obfuscation
```

```powershell
Sử dụng Format String: ("{2}{0}{3}{4}{1}" -f 'Obfus','n','Invoke-','cat','io')
```

Khi chạy trên powershell cli:

```shell
PS C:\Users\trunglt> ("{2}{0}{3}{4}{1}" -f 'Obfus','n','Invoke-','cat','io')
Invoke-Obfuscation
```

**Cách 2: Cộng chuỗi**
Kỹ thuật này thì kinh điển rồi, đơn giản là tách ra thành nhiều sub string và sử dụng "+" để cộng lại thành chuỗi ban đầu:
Ví dụ:

```powershell
String gốc: Invoke-Obfuscation
```

```powershell
Sử dụng Format String: ("Inv" +"oke-" + "Obfusca" + "tion")
```

Khi chạy trên powershell cli:

```shell
PS C:\Users\trunglt> ("Inv" +"oke-" + "Obfusca" + "tion")
Invoke-Obfuscation
```

**Phương án giải quyết:**

- Dùng regex để tìm kiếm các chuỗi string match với 02 cách trên
  String Plus:
  `(\()(\s*)([\'\"][\w\s\+\"\-\'\:]+[\'\"])(\s*)(\))`
  Format String:
  `` (\(\s*[\'\"])({\d+})+[`\"]\s*-[fF]\s*([\'\"][^[\'\"\]]*[\'\"],?)+(\s*\)) ``
- Dùng python subprocess call powershell.exe lên và truyền string match ở bước 1 vào và đọc output
- Replace output ở bước 2 với string match ở bước 1

### Special Characters

Powershell sẽ escape một số Special Characters như sau:

- **`` `0 ``** – Null
- **`` `a ``** – Alert
- **`` `b ``** – Backspace
- **`` `e ``** – Escape
- **`` `f ``** – Form Feed
- **`` `n ``** – New Line
- **`` `r ``** – Carriage Return
- **`` `t ``** – Horizontal Tab
- **`` `u{x} ``** – Unicode Escape Sequence
- **`` `v ``** – Vertical Tab
- **`--%`** – Stop Parsing

Tuy nhiên, nêu sau ký tự **`` ` ``** không phải là các ký tự như trên thì powershell sẽ tự động **_remove_** ký tự đấy đi.
Ví dụ 1:

```console
PS C:\Users\trunglt> Wr`it`e-Host "Hello"
Hello
```

Ví dụ 2:

```console
PS C:\Users\trunglt> Write-Hos`t "Hello"
Write-Hos        : The term 'Write-Hos  ' is not recognized as the name of a cmdlet, function, script file, or operable
program. Check the spelling of the name, or if a path was included, verify that the path is correct and try again.
At line:1 char:1
+ Write-Hos`t "Hello"
+ ~~~~~~~~~~~
    + CategoryInfo          : ObjectNotFound: (Write-Hos        :String) [], CommandNotFoundException
    + FullyQualifiedErrorId : CommandNotFoundException
```

Ở ví dụ 1 `` `i `` và `` `e `` không nằm trong danh sách **_Special Characters_** nên powershell sẽ bỏ qua và thực thi **_Write-Host_** như bình thường
Ở ví dụ 2 thì `` `t `` nằm trong danh sách **_Special Characters_** nên powershell sẽ escape string này thành ký tự **_TAB_** dẫn dến command bị lỗi.

**Phương án giải quyết:**

- Dùng string replace xóa hết các ký tự **_`` ` ``_** là xong :)
- Có thể thêm bước tìm kiếm các **_Special Characters_** trước khi replate để đảm bảo script không bị **_lỗi_** khi đoạn script print ra một cái gì đó kiểu như `` Xuống dòng nhé `n OK `` thì lại thành `Xuống dòng nhé n OK` :D

### Invoke-Expression

Invoke-Obfuscation cung cấp 5 Module bao gồm:

- TOKEN
- AST
- STRING
- ENCODING
- COMPRESS

Module TOKEN và AST :
Bản chất của 2 module này là dùng powershell format string nên có thể dễ dàng xử lý

Dữ liệu mẫu:

![sample script block](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/string_concat_input_script.PNG?raw=true)

Module STRING:

- Concatenate entire command

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/string_concat_output.PNG?raw=true)

- Reorder entire command after concatenating

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/string_reorder_output.png?raw=true)

- Reverse entire command after concatenating

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/string_reverse_output.png?raw=true)

Module ENCODING:

- Encode entire command as ASCII

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/encoding_ascii_output.png?raw=true)

- Encode entire command as Hex

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/encoding_hex_output.png?raw=true)

- Encode entire command as Octal

- Encode entire command as Binary

- Encrypt entire command as SecureString (AES)

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/encoding_securestring_output.png?raw=true)

- Encode entire command as BXOR

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/encoding_bxor_output.png?raw=true)

- Encode entire command as Special Characters

>***Riêng cái này thì chưa tìm được phương án xử lý***
![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/encoding_Special_Characters_output.png?raw=true)

- Encode entire command as Whitespace

![enter image description here](https://github.com/vnStrawHat/Powershell_DOT/blob/master/images/encoding_whitespace_output.png?raw=true)

Như các output trên, chung ta có thể thấy rằng tất cả đều sử dụng IEX để thực thi đoạn script đã được obfuscated.

Có nhiều cách để Invoke-Obfuscation sử dụng **_Invoke-Expression_**:

- `. IEX(Obfuscated_string)`
- `& IEX(Obfuscated_string)`
- `Obfuscated_string | IEX`
- `($var = Obfuscated_string) ; IEX $var`

Chuỗi IEX hoặc Invoke-Expression có thể được obfuscated thành các chuỗi khác nhau như:

- `| .( $EnV:comSPEc[4,15,25]-join'')`
- `.( $pshoMe[21]+$pshOME[30]+'x')`
- `| &( ([StRiNG]$VErboSePreFERenCE)[1,3]+'X'-jOIN'')`
- `| & ((Gv '*mDr*').nAmE[3,11,2]-jOIN'')`
- `set-VARIable u8IZ5 (..snip..snip.. ; . ( $VerbOSEprefErENCE.tOstRInG()[1,3]+'X'-JoIn'') ( -JOiN(cHiLDiTem VaRIAble:U8IZ5).ValUE )`
- `|& ( $pshOmE[4]+$PsHoMe[34]+'X')`
- `& ( $shellId[1]+$sHelLId[13]+'X')`

Tìm hiểu thêm về Invoke-Expression (IEX - [https://ss64.com/ps/invoke-expression.html](https://ss64.com/ps/invoke-expression.html)).
IEX cho phép powershell thực thi một đoạn code được truyền vào. Đoạn code có thể là một chuỗi script block hoặc một biến đã được định nghĩa và cả hai đều phải hợp lệ với PowerShell expression. Điều này có nghĩa là:

- Đoạn code truyền vào cho IEX cần phải là 1 đoạn script block có thể thực thi
- Tất cả các hàm được sử dụng cho việc Obfuscate như replace, reverse, join, concat, decompress, join, bxor, char, toint16... đều xuất hiện trên đoạn code đầu vào cho IEX
- Đoạn code đầu vào cho IEX sẽ có giá trị bằng với đoạn script gốc sau khi thực thi các hàm Obfuscate như replace, reverse, join, concat, decompress, join, bxor, char, toint16...

Đoạn này hơi khó hiểu, đại khái là đang không biết diễn giải như thế nào cho dễ hiểu :D
Sương sương như sau:


Lợi dụng điều đó, thay vì truyền vào cho IEX để thực thi đoạn script block, chúng ta sẽ thay thế IEX bằng một hàm khác để print đoạn script block đấy ra nhưng vẫn thực thi các hàm bên trong. 

Tại sao lại focus vào IEX thay vì focus vào xử lý các hàm sử dụng để obfuscate ?

- Powershell sẽ tự động thực thi các hàm obfuscate và cho ra clear output mà không cần phải xử lý ở ngoài.
- Không cần quan tâm hàm obfuscate là hàm gì, mọi việc đã có powershell.exe lo :)

Một số option sau có thể chọn:

- `Out-File -InputObject <code> -FilePath <đường dẫn lưu file out put>` => output to file
- `Write-Host -Object <code>` => output to console
- `Write-Output -InputObject <code>` => output to console
- `Out-String -InputObject <code>` => output to console

Sau khá nhiều thử nghiệm thì phát hiện ra sử dụng **_output to file_** là OK nhất, với một số case thì sử dụng **_output to console_** gây ra hiện tượng bị mất ký tự xuống dòng `\r` `\n` dẫn đến format đoạn script gốc bị sai lệch.
