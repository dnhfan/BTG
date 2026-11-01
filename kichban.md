# KỊCH BẢN VIDEO GIỚI THIỆU BTG — BẢN 10–15 PHÚT (GỬI THẦY, BÀI TẬP LỚN GIỮA KÌ)

## Thông tin chung

- **Dự án:** BTG — Black-box Test Generator, phần mềm sinh test case tự động cho hàm Python bằng phương pháp kiểm thử hộp đen
- **Môn học:** Đánh giá kiểm định chất lượng phần mềm
- **Giảng viên hướng dẫn:** TS. Trịnh Thanh Bình
- **Nhóm:** Phạm Lê Đình An, Nguyễn Bá Thiện, Đặng Đắc Tú, Hà Lê Quang Minh
- **Người dẫn trong video:** Nguyễn Bá Thiện (đại diện nhóm, dẫn toàn bộ video)
- **Hình thức:** Quay màn hình ứng dụng desktop + lời dẫn, không cần quay mặt
- **Thời lượng mục tiêu:** khoảng 12 phút 30 giây (nằm trong khung 10–15 phút thầy yêu cầu)
- **Hàm demo xuyên suốt video:** `register(username, age, role, active)` trong `examples/sample_function.py`
  - `username`: chuỗi dài 3–20 ký tự
  - `age`: số nguyên 18–60
  - `role`: `admin`, `user`, `guest`
  - `active`: `True` / `False`
- **Số liệu đã kiểm chứng, dùng trong video (không nói số khác):** sinh 38 test case cho hàm `register`; file kiểm thử sinh ra chạy đạt 38/38 khi đối chiếu với hàm mẫu; lõi sinh test case có 13 unit test và đều đạt; thời gian sinh 38 case khoảng 0,003 giây (yêu cầu SRS dưới 2 giây).

## Chuẩn bị trước khi quay

- Mở sẵn ứng dụng BTG (CustomTkinter desktop, `python app.py`), phóng to cửa sổ, để chế độ Sáng cho chữ rõ khi quay, tắt thông báo trên máy.
- Chuẩn bị sẵn 2 file: file hàm mẫu `register` và file Hàm tham chiếu của hàm đó (có thể dùng chính `sample_function.py`).
- Chạy thử trước một lần toàn bộ luồng: nhập spec / tải file .py → sinh test case → nạp Hàm tham chiếu → chạy kiểm thử → xuất CSV, Excel, `test_generated.py` → chạy `pytest` file vừa sinh. Chỉ quay khi luồng thử đã chạy trơn.
- Nói chậm, rõ, nhìn vào nội dung đang chỉ trên màn hình thay vì đọc thuộc lòng từng chữ. Lời thoại dưới đây viết theo lối nói, cứ nói tự nhiên theo ý đó là đủ, không cần đọc nguyên văn chữ trên màn hình.

## Bảng phân cảnh và thời lượng

| Cảnh | Nội dung                                            | Thời lượng  |
| ---- | --------------------------------------------------- | ----------- |
| 1    | Mở đầu, giới thiệu nhóm và mục tiêu                 | 0:00–1:00   |
| 2    | Vấn đề đặt ra: vì sao viết tay dễ sót               | 1:00–2:30   |
| 3    | Cơ sở lý thuyết: EP, BVA, Pairwise                  | 2:30–4:30   |
| 4    | Demo 1: nhập spec, tải file .py, sinh 38 test case  | 4:30–6:30   |
| 5    | Demo 2: Hàm tham chiếu, sửa Expected, chạy kiểm thử | 6:30–8:30   |
| 6    | Demo 3: xuất CSV, Excel, pytest và kiểm chứng       | 8:30–10:00  |
| 7    | Kiến trúc, phạm vi và hạn chế nói thẳng             | 10:00–11:30 |
| 8    | Kết luận và cảm ơn thầy                             | 11:30–12:30 |

---

## Cảnh 1 — Mở đầu (0:00–1:00)

**Hình ảnh:** Màn hình tiêu đề: tên đề tài BTG, tên môn, tên nhóm, tên thầy hướng dẫn. Sau đó chuyển sang giao diện chính của BTG.

**Lời thoại:**

> Em chào thầy ạ. Em là Nguyễn Bá Thiện, đại diện nhóm An, Thiện, Tú, Minh. Hôm nay nhóm em xin giới thiệu bài tập lớn giữa kì của nhóm: BTG, viết tắt của Black-box Test Generator,
> một phần mềm sinh test case tự động cho các hàm Python, làm theo phương pháp kiểm thử hộp đen.
>
> Trong khoảng 12 phút tới, em sẽ trình bày theo 4 phần chính. Thứ nhất là vì sao nhóm em làm công cụ này. Thứ hai là 3 kỹ thuật hộp đen mà công cụ dùng. Thứ ba là demo trực tiếp trên một hàm đăng ký mẫu, từ lúc sinh test case, đối chiếu kết quả, cho đến lúc xuất file dùng được ngay. Và cuối cùng là phạm vi, hạn chế của công cụ, để thầy đánh giá đúng những gì nhóm em đã làm được và chưa làm được.

**Lưu ý quay:** Đọc tên nhóm chậm một nhịp. Đừng dừng quá lâu ở màn hình tiêu đề, chuyển sang giao diện chính ngay khi nói đến câu “4 phần chính” để thầy thấy sản phẩm thật từ đầu.

---

## Cảnh 2 — Vấn đề đặt ra (1:00–2:30)

**Hình ảnh:** Một form đăng ký đơn giản, hoặc bảng đặc tả của hàm `register`: tên đăng nhập, tuổi, vai trò, trạng thái hoạt động. Chỉ vào từng dòng đặc tả khi nhắc đến.

**Lời thoại:**

> Để thấy vì sao nhóm em làm công cụ này, thầy hãy nhìn vào một hàm đăng ký tưởng như rất đơn giản. Hàm này nhận 4 đầu vào. Tên đăng nhập phải dài từ 3 đến 20 ký tự. Tuổi phải từ 18 đến 60. Vai trò chỉ được là admin, user hoặc guest. Và trạng thái hoạt động chỉ có đúng hoặc sai.
>
> Nghe thì đơn giản, nhưng chỉ cần một chỗ làm sai, hệ thống đã có thể gặp rắc rối: tên quá ngắn vẫn đăng ký được, tuổi nằm ngoài độ tuổi cho phép vẫn lọt qua, vai trò không có trong danh sách vẫn được chấp nhận, hoặc một tổ hợp lạ của nhiều ô nhập cùng lúc mới gây lỗi, còn thử từng ô riêng thì không thấy gì.
>
> Viết test case bằng tay cho những trường hợp đó vừa tốn thời gian, vừa rất dễ sót. Người viết hay sót nhất ở 2 chỗ: các trường hợp ở ranh giới giữa đúng và sai, ví dụ tuổi 17 và 18, tuổi 60 và 61, tên dài 2 ký tự và 3 ký tự; và các tổ hợp của nhiều tham số, vì thử mọi tổ hợp thì số lượng tăng rất nhanh, còn thử thiếu thì lại bỏ lọt lỗi tương tác. Đó chính là bài toán mà nhóm em muốn giải quyết: làm sao sinh được một bộ test gọn, mà vẫn bao quát được các vùng giá trị, các biên và các tổ hợp quan trọng.

**Lưu ý quay:** Khi nói “tuổi 17 và 18” thì chỉ đúng vào dòng tuổi trên bảng đặc tả. Đoạn này chưa cần mở BTG, chỉ cần bảng đặc tả rõ, dễ đọc.

---

## Cảnh 3 — Cơ sở lý thuyết: 3 kỹ thuật hộp đen (2:30–4:30)

**Hình ảnh:** Slide hoặc bảng đơn giản, 3 hàng tương ứng 3 kỹ thuật, mỗi hàng có 1 ví dụ lấy từ hàm `register`. Không cần slide cầu kỳ, chỉ cần chữ lớn, đọc được.

**Lời thoại:**

> Giải pháp của nhóm em là BTG. Thay vì để người kiểm thử tự nghĩ từng trường hợp, người dùng chỉ cần mô tả hàm cần kiểm thử: hàm nhận những đầu vào nào, mỗi đầu vào được phép nằm trong khoảng nào. Từ mô tả đó, BTG sẽ tự sinh test case bằng 3 kỹ thuật của kiểm thử hộp đen. Điểm quan trọng là BTG chỉ dựa vào mô tả đầu vào, không cần đọc sâu code bên trong hàm, nên đây đúng là kiểm thử hộp đen.
>
> Kỹ thuật thứ nhất là Equivalence Partitioning, tức là phân vùng tương đương. Ý tưởng rất đơn giản: chia miền đầu vào thành các vùng, rồi lấy đại diện cho từng vùng, thay vì thử mọi giá trị. Ví dụ với tuổi từ 18 đến 60, ta có vùng hợp lệ là 18 đến 60, vùng không hợp lệ là dưới 18 và trên 60. Chỉ cần thử một giá trị đại diện trong mỗi vùng, cộng thêm các giá trị không hợp lệ theo từng tham số, là đã bao quát được các vùng chính.
>
> Kỹ thuật thứ hai là Boundary Value Analysis, tức là phân tích giá trị biên. Lỗi rất hay nằm ngay tại biên, ngay chỗ điều kiện đổi từ đúng sang sai, ví dụ lập trình viên viết nhầm dấu nhỏ hơn thành nhỏ hơn hoặc bằng. Vì vậy, với mỗi biên, BTG thử cả giá trị tại biên và 2 giá trị sát biên 2 phía. Với tuổi, đó là 17, 18, 19 ở biên dưới và 59, 60, 61 ở biên trên. Tương tự với độ dài tên đăng nhập, BTG thử tên dài 2, 3, 4 ký tự ở biên dưới và 19, 20, 21 ký tự ở biên trên.
>
> Kỹ thuật thứ ba là Pairwise Testing, tức là kiểm thử theo cặp. Khi hàm có nhiều tham số, thử mọi tổ hợp là không khả thi, nhưng lỗi tương tác thường chỉ liên quan đến 2 tham số cùng lúc. Vì vậy BTG sinh các tổ hợp sao cho mọi cặp giá trị của mọi cặp tham số đều xuất hiện ít nhất một lần, thay vì thử mọi tổ hợp. Hàm `register` có 4 tham số nên BTG áp dụng cả 3 kỹ thuật này. Cuối cùng, các trường hợp trùng nhau về đầu vào được gộp lại, để bộ test gọn mà vẫn đủ các vùng, các biên và các cặp giá trị quan trọng. Mỗi test case sinh ra đều ghi rõ lý do vì sao nó được chọn, ví dụ trường hợp này kiểm tra tuổi ngay dưới biên, trường hợp kia kiểm tra tên quá ngắn.

**Lưu ý quay:** Đoạn lý thuyết này là chỗ dễ nói nhanh, nói lướt nhất. Nói chậm lại, mỗi kỹ thuật dừng một nhịp sau câu ví dụ. Thầy đánh giá bài tập lớn qua việc nhóm có hiểu kỹ thuật hay không, nên đừng rút ngắn cảnh này để lấy thời gian cho demo.

---

## Cảnh 4 — Demo 1: Nhập spec và sinh test case (4:30–6:30)

**Hình ảnh:** Quay thao tác thật trên BTG: mở form nhập, thêm 4 tham số, hoặc tải file `.py` mẫu để ứng dụng tự trích xuất bằng AST. Bấm sinh test case, bảng test case hiện ra. Phóng to bảng, chỉ vào 2–3 dòng tiêu biểu.

**Lời thoại:**

> Bây giờ em xin demo trực tiếp. Trên BTG, người dùng có 2 cách mô tả hàm. Cách thứ nhất là nhập trực tiếp trên form: tên hàm, thêm từng tham số, chọn kiểu dữ liệu, nhập khoảng giá trị, độ dài, danh sách giá trị cho enum, hoặc cho phép rỗng hay không. BTG hỗ trợ các kiểu int, float, string, enum và bool; với string còn cấu hình được độ dài và biểu thức chính quy.
>
> Cách thứ hai, nhanh hơn, là tải lên file `.py` chứa hàm cần kiểm thử. BTG sẽ đọc file bằng AST, tức là đọc cấu trúc code, để tự trích xuất tên hàm, tên tham số và type hint, kể cả `Literal` thì được chuyển thành enum. Sau đó người dùng vẫn kiểm tra và sửa lại khoảng giá trị trên form trước khi sinh. Trước khi sinh, BTG còn kiểm tra tính hợp lệ của đặc tả, ví dụ báo lỗi khi giá trị nhỏ nhất lớn hơn giá trị lớn nhất, khi biểu thức chính quy sai, hoặc khi trùng tên tham số, để không sinh test case từ một đặc tả sai ngay từ đầu.
>
> Em bấm sinh test case. Như thầy thấy, hệ thống đã sinh ra 38 trường hợp cho hàm `register`. Em phóng to bảng để thầy xem rõ hơn. Mỗi dòng là một test case, có mã, các đầu vào, kết quả mong đợi, kỹ thuật đã sinh ra nó và lý do chọn. Ví dụ dòng này kiểm tra tuổi ngay dưới biên, dòng này kiểm tra tên quá ngắn, dòng này là một tổ hợp theo cặp giữa vai trò và trạng thái hoạt động. Nếu thầy để ý, sẽ thấy các trường hợp trùng đầu vào đã được gộp, nên 38 trường hợp này là 38 bộ đầu vào khác nhau, không bị lặp.

**Lưu ý quay:** Đây là cảnh quan trọng nhất, đừng bấm quá nhanh. Sau khi bấm sinh, dừng 2–3 giây để bảng hiện đủ rồi mới nói tiếp. Khi chỉ vào bảng, dừng 2–3 giây ở mỗi dòng tiêu biểu để thầy kịp đọc, đừng lướt nhanh qua bảng.

---

## Cảnh 5 — Demo 2: Hàm tham chiếu và chạy kiểm thử (6:30–8:30)

**Hình ảnh:** Nạp file Hàm tham chiếu, nhấp đúp sửa một kết quả mong đợi, bấm Run Tests, bảng kết quả Pass/Fail/Skipped hiện ra, kèm tỉ lệ đạt.

**Lời thoại:**

> Sinh xong test case thì cần biết hàm làm đúng hay sai. Muốn vậy phải có đáp án mẫu để đối chiếu. Nhóm em dùng một hàm đúng, gọi là Hàm tham chiếu, để làm đáp án mẫu. Người dùng có thể dán code của hàm đó vào ứng dụng, hoặc nạp từ một file `.py` riêng. BTG sẽ chạy Hàm tham chiếu với từng bộ đầu vào để tự điền kết quả đúng cho từng test case.
>
> Nếu trường hợp nào chưa có đáp án mẫu, người dùng có thể nhấp đúp trực tiếp vào cột kết quả mong đợi hoặc ngoại lệ mong đợi của trường hợp đó để sửa tay. Việc này quan trọng vì trong thực tế, không phải lúc nào cũng có sẵn một hàm đúng để đối chiếu.
>
> Em bấm chạy kiểm thử. Hệ thống đưa từng đầu vào vào hàm đối chiếu, so sánh với kết quả mong đợi và kết luận từng trường hợp là đạt, không đạt, hay bỏ qua khi không có đáp án để đối chiếu. Tỉ lệ đạt được tính chỉ trên những trường hợp có đối chiếu, còn các trường hợp bỏ qua thì không tính vào, để con số này phản ánh đúng kết quả kiểm thử, không bị pha loãng bởi những trường hợp chưa có đáp án.
>
> Một điểm nữa em muốn nhấn mạnh: nếu người dùng sinh lại bộ test mới, hoặc sửa một kết quả mong đợi sau khi đã chạy, thì kết quả chạy cũ sẽ bị hủy hiệu lực, để không xuất báo cáo với trạng thái cũ đã lỗi thời. Đây là chỗ nhóm em làm cẩn thận để tránh báo cáo sai.

**Lưu ý quay:** Cố tình sửa 1 giá trị mong đợi bằng nhấp đúp ngay trên video, đừng chỉ nói miệng. Thầy sẽ tin tính năng này hơn khi thấy thao tác thật. Sau khi bấm chạy, để bảng kết quả hiện rõ rồi mới đọc tỉ lệ.

---

## Cảnh 6 — Demo 3: Xuất kết quả và kiểm chứng (8:30–10:00)

**Hình ảnh:** Bấm xuất CSV, mở nhanh file CSV; bấm xuất Excel; bấm xuất file kiểm thử, mở file `test_generated.py`, chạy `pytest` và để kết quả hiện trên màn hình.

**Lời thoại:**

> Cuối cùng, bộ test có thể xuất ra để dùng lại và nộp kèm báo cáo. BTG xuất được 3 dạng. Thứ nhất là bảng tính CSV và Excel, ghi đầy đủ mã test case, đầu vào, kết quả mong đợi, kỹ thuật và lý do. Sau khi đã chạy kiểm thử, file xuất ra còn kèm thêm 3 cột là kết quả thực tế, ngoại lệ thực tế và trạng thái đạt hay không đạt, nên file này dùng được ngay như một báo cáo test hoàn chỉnh.
>
> Thứ hai là file kiểm thử `test_generated.py`, dùng `@pytest.mark.parametrize`, chạy được ngay mà không cần sửa gì thêm. Em mở nhanh file này để thầy thấy mỗi test case đã trở thành một trường hợp kiểm thử trong code, và em chạy thử ngay trên video.
>
> Với hàm mẫu vừa rồi, file kiểm thử sinh ra chạy đạt cả 38 trên 38 trường hợp khi đối chiếu với hàm mẫu. Về độ tin cậy của chính công cụ, phần lõi sinh test case của nhóm em cũng đã được kiểm tra bằng 13 test tự động và đều đạt, để đảm bảo cùng một mô tả thì luôn cho ra cùng một bộ test. Và về hiệu năng, việc sinh 38 test case cho hàm 4 tham số này chỉ mất khoảng 0,003 giây, thấp hơn nhiều so với yêu cầu dưới 2 giây trong tài liệu SRS.

**Lưu ý quay:** Đừng chỉ bấm xuất rồi nói “đã xuất xong”. Mở thật file CSV và file `test_generated.py` lên, để thầy thấy nội dung bên trong. Kết quả `pytest` phải hiện rõ dòng 38 passed, quay chậm ở đoạn này.

---

## Cảnh 7 — Kiến trúc, phạm vi và hạn chế (10:00–11:30)

**Hình ảnh:** Sơ đồ đơn giản hoặc quay lại giao diện chính, chỉ vào từng khối chức năng khi nhắc đến. Không cần thao tác thêm.

**Lời thoại:**

> Em xin nói thêm một chút về cách nhóm em tổ chức code và phạm vi của công cụ, để thầy đánh giá đúng. Về kiến trúc, BTG tách thành các lớp rõ ràng: một lớp đọc file `.py` bằng AST, một lớp kiểm tra đặc tả, một lớp sinh test case theo 3 kỹ thuật vừa nói, một lớp chạy Hàm tham chiếu và tính tỉ lệ đạt, và một lớp xuất file. Lớp giao diện desktop viết bằng CustomTkinter, tách riêng với lõi sinh test case, nên lõi có thể chạy độc lập bằng dòng lệnh mà không cần mở giao diện.
>
> Nhóm em cũng xin nói thẳng hạn chế của công cụ. Thứ nhất, BTG hiện chỉ xét các hàm viết ở cấp ngoài cùng của file, chưa xử lý hàm lồng nhau hay hàm trong class một cách đầy đủ. Thứ hai, chất lượng bộ test phụ thuộc nhiều vào việc mô tả đầu vào có chính xác hay không: nếu người dùng nhập sai khoảng giá trị thì bộ test sinh ra cũng sẽ sai theo. Thứ ba, Hàm tham chiếu chỉ nên là code mà người dùng tin cậy, vì hệ thống chạy trực tiếp code đó trên máy. Và thứ tư, BTG không xây đồ thị luồng điều khiển, không dùng AI để sinh mã, và không đo mức độ bao phủ theo từng dòng code hay từng nhánh rẽ bên trong hàm, vì những việc đó nằm ngoài phạm vi kiểm thử hộp đen mà nhóm em đã đặt ra trong SRS.
>
> Nói cách khác, BTG làm tốt đúng một việc mà SRS yêu cầu: từ mô tả đầu vào, sinh ra một bộ test hộp đen gọn, có lý do rõ ràng, chạy được và xuất được ngay.

**Lưu ý quay:** Đoạn hạn chế đừng nói nhanh cho qua. Nói thẳng, tốc độ bình thường, vì thầy thường đánh giá cao nhóm tự thấy được giới hạn của mình hơn là nhóm chỉ khoe ưu điểm.

---

## Cảnh 8 — Kết luận và cảm ơn (11:30–12:30)

**Hình ảnh:** Quay lại màn hình tiêu đề hoặc giao diện chính, không cần thao tác thêm.

**Lời thoại:**

> Tóm lại, BTG là một công cụ desktop giúp người kiểm thử tiết kiệm thời gian viết test case bằng tay, mà vẫn bao quát được các vùng giá trị, các giá trị biên và các tổ hợp theo cặp, là những chỗ dễ sót lỗi nhất. Người dùng chỉ cần mô tả hàm, BTG sinh test case có lý do rõ ràng, đối chiếu bằng Hàm tham chiếu, chạy kiểm thử và xuất ra file dùng được ngay.
>
> Nhóm em xin cảm ơn thầy đã theo dõi. Nhóm em rất mong nhận được góp ý của thầy để hoàn thiện bài tập lớn tốt hơn, đặc biệt là ở phần xử lý hàm phức tạp hơn và cách trình bày bộ test sao cho dễ đọc hơn. Em xin cảm ơn thầy ạ.

**Lưu ý quay:** Kết thúc bằng màn hình tiêu đề có tên nhóm, để thầy chụp lại hoặc ghi nhớ tên đề tài khi chấm. Kiểm tra lại trước khi gửi: tiếng có rõ không, chữ trên màn hình có đọc được không, và file video có mở được bình thường không.

---

## Ghi chú khi quay và dựng

- Nếu một thao tác trên màn hình bị lỗi giữa chừng, đừng quay lại từ đầu: cứ nói rõ “đoạn này em làm lại” rồi quay tiếp, lúc dựng video cắt đoạn lỗi đi là được.
- Ưu tiên quay 1 lần liền mạch theo đúng thứ tự 8 cảnh, vì thứ tự này đã đi từ vấn đề → lý thuyết → demo → kiểm chứng → hạn chế → kết luận.
- Nếu video quay xong dài hơn 13 phút, cắt bớt ở Cảnh 3 bằng cách rút 1 ví dụ biên, đừng cắt Cảnh 4, 5, 6 vì đó là bằng chứng sản phẩm chạy thật.
- Nếu video ngắn hơn 10 phút, kéo dài Cảnh 4 bằng cách chỉ thêm 1–2 dòng test case tiêu biểu nữa, đừng nói nhanh hơn để nhồi thêm nội dung.
- Kiểm tra cuối: tên đề tài, tên nhóm, tên thầy đúng chính tả; thuật ngữ dùng thống nhất là “bài tập lớn” và “Hàm tham chiếu” trong toàn bộ video.
