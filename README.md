
# Powershell_DOT (Powershell De-Obfuscation Tool)

## How to use ?

```shell
python powershelldf.py -h
```

## The Goal ?

Tool này sinh ra để defeat Invoke-Obfuscation :confused:

## The history ?

> Powershell attack đang hot trend gần đây bên quyết đị bú frame tí.

Trong quá trình thực hiện điều tra một số case APT, mình gặp khá nhiều các trường hợp Attacker sử dụng powershell one-liner để cài backdoor vào máy tính người dùng và máy chủ. Dĩ nhiên đa số các trường hợp đoạn powershell đều bị obfuscated. Cá biệt có những case powershell script bị obfuscated đến 7 lần.

Ban đầu mình viết tool này để giải quyết mấy trường hợp các biệt trên. Nhưng sau khi thử nghiệm trên nhiều mẫu powershell obfuscated khác nhau thì nhận ra: "tool mình viết hoạt động tốt hơn mong đợi :D" nên quyết định thêm một vài tính năng nữa nhìn cho nó xịn xò hơn. Ví dụ ứng dụng Machine Learning vào việc Deobfuscate. Nghe có vẻ vãi nhỉ ? watch till the end :shit:

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
- Có thể thêm bước tìm kiếm các **_Special Characters_** trước khi replate để đảm bảo script không bị **_lỗi_** khi đoạn script print ra một cái gì đó kiểu như `` Xuống dòng nhé `n OK `` thì lại thành `Xuống dòng nhé n OK` :grin:

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
- Tất cả các hàm được sử dụng cho việc Obfuscate như `replace` `reverse` `join` `concat` `decompress` `join` `bxor` `[char]` `toint16`... đều xuất hiện trên đoạn code đầu vào cho IEX
- Đoạn code đầu vào cho IEX sẽ có giá trị bằng với đoạn script gốc sau khi thực thi các hàm Obfuscate như `replace` `reverse` `join` `concat` `decompress` `join` `bxor` `[char]` `toint16`...

Đoạn này hơi khó hiểu, đại khái là đang không biết diễn giải như thế nào cho dễ hiểu :confused: Sương sương như ví dụ sau:

```powershell
IEX( ( '36{78Q55@32t61_91{99@104X97{114Q91-32t93}32t93}32t34@110m111@105}115X115-101m114_112@120@69-45{101@107X111m118m110-73Q124Q32X41Q57@51-93Q114_97_104t67t91{44V39Q112_81t109@39}101{99@97}108{112}101}82_45m32_32X52{51Q93m114@97-104{67t91t44t39V98t103V48t39-101}99}97V108}112t101_82_45{32@41X39{41_112t81_109_39m43{39-110t101@112{81t39X43@39t109_43t112_81Q109t101X39Q43m39}114Q71_112{81m109m39@43X39V32Q40}32m39_43_39{114-111m108t111t67{100m110{117Q39_43m39-111-114Q103_101t114@39m43-39{111t70-45}32m41}98{103V48V110Q98t103{48@39{43{39-43{32t98m103_48{111@105t98@103V48-39@43{39_32-32V43V32}32t98t103@48X116m97V99t98X103t48_39V43m39@43-39X43Q39_98@103@48}115V117V102Q98V79m45@98m39Q43{39X103_39X43Q39V48}43-39}43t39}98-103{48V101_107Q39t43X39_111X118X110V39X43}39t98_103{48@43}32_98{103}48{73{98-39@43t39m103_39}43{39{48Q32t39X43X39-32{40V32t41{39Q43V39m98X103{39_43V39{48-116{115Q79{39_43_39}98}103m48{39Q43t39X32X43{32_98@103-39@43m39X48_72-39_43t39V45m39t43Q39_101Q98}103_48-32_39Q43V39V32t39V43}39m43Q32V98X39Q43_39@103_48V39@43Q39@116X73t82V119m98-39{43_39}103Q48X40_46_32m39}40_40{34t59m91@65V114V114@97_121}93Q58Q58V82Q101Q118Q101{114}115_101m40_36_78m55@32t41t32-59{32}73{69V88m32{40t36V78t55}45Q74m111@105-110m32X39V39-32}41'.SpLiT( '{_Q-@t}mXV' ) |ForEach-Object { ([Int]$_ -AS [Char]) } ) -Join'' )
```
Phía trên là một script powershell đã bị obfuscate

Thay vì thực thi đoạn script block bên trong bằng IEX, chung ta sẽ thay IEX bằng Write-Host để print giá trị của chuỗi script block ra màn hình:
```console
PS C:\>Write-Host(  ( '36{78Q55@32t61_91{99@104X97{114Q91-32t93}32t93}32t34@110m111@105}115X115-101m114_112@120@69-45{101@107X111m118m110-73Q124Q32X41Q57@51-93Q114_97_104t67t91{44V39Q112_81t109@39}101{99@97}108{112}101}82_45m32_32X52{51Q93m114@97-104{67t91t44t39V98t103V48t39-101}99}97V108}112t101_82_45{32@41X39{41_112t81_109_39m43{39-110t101@112{81t39X43@39t109_43t112_81Q109t101X39Q43m39}114Q71_112{81m109m39@43X39V32Q40}32m39_43_39{114-111m108t111t67{100m110{117Q39_43m39-111-114Q103_101t114@39m43-39{111t70-45}32m41}98{103V48V110Q98t103{48@39{43{39-43{32t98m103_48{111@105t98@103V48-39@43{39_32-32V43V32}32t98t103@48X116m97V99t98X103t48_39V43m39@43-39X43Q39_98@103@48}115V117V102Q98V79m45@98m39Q43{39X103_39X43Q39V48}43-39}43t39}98-103{48V101_107Q39t43X39_111X118X110V39X43}39t98_103{48@43}32_98{103}48{73{98-39@43t39m103_39}43{39{48Q32t39X43X39-32{40V32t41{39Q43V39m98X103{39_43V39{48-116{115Q79{39_43_39}98}103m48{39Q43t39X32X43{32_98@103-39@43m39X48_72-39_43t39V45m39t43Q39_101Q98}103_48-32_39Q43V39V32t39V43}39m43Q32V98X39Q43_39@103_48V39@43Q39@116X73t82V119m98-39{43_39}103Q48X40_46_32m39}40_40{34t59m91@65V114V114@97_121}93Q58Q58V82Q101Q118Q101{114}115_101m40_36_78m55@32t41t32-59{32}73{69V88m32{40t36V78t55}45Q74m111@105-110m32X39V39-32}41'.SpLiT( '{_Q-@t}mXV' ) |ForEach-Object { ([Int]$_ -AS [Char]) } ) -Join'')

$N7 =[char[ ] ] "noisserpxE-ekovnI| )93]rahC[,'pQm'ecalpeR-  43]rahC[,'bg0'ecalpeR- )')pQm'+'nepQ'+'m+pQme'+'rGpQm'+' ( '+'roloCdnu'+'orger'+'oF- )bg0nbg0'+'+ bg0oibg0'+'  +  bg0tacbg0'+'+'+'bg0sufbO-b'+'g'+'0+'+'bg0ek'+'ovn'+'bg0+ bg0Ib'+'g'+'0 '+' ( )'+'bg'+'0tsO'+'bg0'+' + bg'+'0H'+'-'+'ebg0 '+' '+'+ b'+'g0'+'tIRwb'+'g0(. '((";[Array]::Reverse($N7 ) ; IEX ($N7-Join '' )
```

Đoạn output script định nghĩa một biến có tên là `$N7`, sau đó biến này được truyền vào cho IEX để thực thi. Thử print biến `$N7` bằng cách thay IEX bằng Write-Host ta có kết quả như sau
```console
PS C:\> $N7 =[char[ ] ] "noisserpxE-ekovnI| )93]rahC[,'pQm'ecalpeR-  43]rahC[,'bg0'ecalpeR- )')pQm'+'nepQ'+'m+pQme'+'rGpQm'+' ( '+'roloCdnu'+'orger'+'oF- )bg0nbg0'+'+ bg0oibg0'+'  +  bg0tacbg0'+'+'+'bg0sufbO-b'+'g'+'0+'+'bg0ek'+'ovn'+'bg0+ bg0Ib'+'g'+'0 '+' ( )'+'bg'+'0tsO'+'bg0'+' + bg'+'0H'+'-'+'ebg0 '+' '+'+ b'+'g0'+'tIRwb'+'g0(. '((";[Array]::Reverse($N7 ) ; Write-Host ($N7-Join '' )

((' .(0g'+'bwRIt'+'0g'+'b +'+' '+' 0gbe'+'-'+'H0'+'gb + '+'0gb'+'Ost0'+'gb'+') ( '+' 0'+'g'+'bI0gb +0gb'+'nvo'+'ke0gb'+'+0'+'g'+'b-Obfus0gb'+'+'+'0gbcat0gb  +  '+'0gbio0gb +'+'0gbn0gb) -Fo'+'regro'+'undColor'+' ( '+'mQpGr'+'emQp+m'+'Qpen'+'mQp)') -Replace'0gb',[Char]34  -Replace'mQp',[Char]39) |Invoke-Expression
```

Thấy sự xuất hiện của Invoke-Expression. tiếp tục thay Invoke-Expression bằng Write-Host ta có kết quả như sau:

```console
PS C:\> ((' .(0g'+'bwRIt'+'0g'+'b +'+' '+' 0gbe'+'-'+'H0'+'gb + '+'0gb'+'Ost0'+'gb'+') ( '+' 0'+'g'+'bI0gb +0gb'+'nvo'+'ke0gb'+'+0'+'g'+'b-Obfus0gb'+'+'+'0gbcat0gb  +  '+'0gbio0gb +'+'0gbn0gb) -Fo'+'regro'+'undColor'+' ( '+'mQpGr'+'emQp+m'+'Qpen'+'mQp)') -Replace'0gb',[Char]34  -Replace'mQp',[Char]39)| Write-Host
 
 .("wRIt" +  "e-H" + "Ost") (  "I" +"nvoke"+"-Obfus"+"cat"  +  "io" +"n") -ForegroundColor ( 'Gre'+'en')
```
Dễ nhận thấy đoạn output sử dụng string concat. Sau khi cộng các chuỗi lại ta có đoạn script block gốc như sau:
```powershell
Write-Host "Invoke-Obfuscation" -ForegroundColor Green
```

Qua ví dụ trên chung ta có thể thấy:

- Đoạn script block được truyền vào cho IEX chắc chắn thực thi được
- Các hàm như `replace` `reverse` `join` `concat` `decompress` `join` `bxor` `[char]` `toint16`... sẽ được powershell thực thi khi thực hiện print đoạn script block đấy ra màn hình thay thì thực thi bằng IEX

Lợi dụng điều đó, thay vì truyền vào cho IEX để thực thi đoạn script block, chúng ta sẽ thay thế IEX bằng một hàm khác để print đoạn script block đấy ra mà không thực thi cả cụm script block đó.

Tại sao lại focus vào IEX thay vì focus vào xử lý các hàm sử dụng để obfuscate ?
- xử lý các hàm `replace` `reverse` `join` `concat` `decompress` `join` `bxor` `[char]` `toint16` quá phưc tạp
- Powershell sẽ tự động thực thi các hàm obfuscate và cho ra clear output mà không cần phải xử lý gì thêm khi print đoạn script block ra ngoài màn hình
- Không cần quan tâm hàm obfuscate là hàm gì, mọi việc đã có powershell.exe lo :kissing:

Một số option sau có thể chọn:

- `Out-File -InputObject <code> -FilePath <đường dẫn lưu file out put>` => output to file
- `Write-Host -Object <code>` => output to console
- `Write-Output -InputObject <code>` => output to console
- `Out-String -InputObject <code>` => output to console

Sau khá nhiều thử nghiệm thì phát hiện ra sử dụng **_output to file_** là OK nhất, với một số case thì sử dụng **_output to console_** gây ra hiện tượng bị mất ký tự xuống dòng `\r` `\n` dẫn đến format đoạn script gốc bị sai lệch.
