// src/components/Cart/Cart.js
import React, { useState, useEffect, useCallback } from 'react'; // Thêm useCallback
import './Cart.css';

// Thay thế bằng URL backend FastAPI của bạn
const API_BASE_URL = 'http://localhost:8000';

// Giả sử user_id cố định là 1 cho ví dụ này
const USER_ID = 1;

function Cart() {
  const [cartItems, setCartItems] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // 1. Đưa logic fetch ra ngoài và bọc bằng useCallback
  const fetchCartData = useCallback(async () => {
    setIsLoading(true);
    setError(null); // Reset lỗi trước mỗi lần fetch

    try {
      // Gọi API GET để lấy dữ liệu giỏ hàng
      const response = await fetch(`${API_BASE_URL}/api/cart?user_id=${USER_ID}`);

      if (!response.ok) {
        let errorDetail = `HTTP error! status: ${response.status}`;
        try {
          // Cố gắng đọc lỗi chi tiết từ server nếu có
          const errorData = await response.json();
          errorDetail = errorData.detail || errorDetail;
        } catch (e) {
          // Không đọc được JSON hoặc không có detail, kiểm tra text
            try {
                const textResponse = await response.text();
                if (textResponse === "Fail to get orders!") {
                     errorDetail = "Không thể lấy danh sách đơn hàng từ server.";
                 }
            } catch (textErr) {
                 // Bỏ qua lỗi đọc text
            }
        }
        throw new Error(errorDetail);
      }

      // Nếu response OK (status 200-299)
      const data = await response.json();

      // Xử lý dữ liệu trả về
      if (Array.isArray(data)) {
        setCartItems(
          data.map((item, index) => ({
            stt: index + 1,
            // Cập nhật các key dựa trên dữ liệu thực tế từ API của bạn
            id: item.id, // Giả sử có ID để dùng làm key
            ten: item.product_name || `Sản phẩm ${item.id || index}`,
            so_luong: item.quantity,
            don_gia: item.price || item.total_amount, // Ưu tiên price nếu có, hoặc total_amount
          }))
        );
      } else if (typeof data === 'string' && data === "Fail to get orders!") {
         // Trường hợp server trả về chuỗi lỗi với status OK (hơi lạ nhưng xử lý)
         console.warn("Server trả về 'Fail to get orders!' với status OK.");
         setCartItems([]); // Hiển thị giỏ hàng rỗng
         setError("Server báo không thể lấy đơn hàng."); // Có thể set lỗi nhẹ
      }
       else {
        // Trường hợp dữ liệu không phải mảng và không phải chuỗi lỗi đã biết
        console.warn("Dữ liệu giỏ hàng trả về không phải là một mảng:", data);
        setCartItems([]); // Hiển thị giỏ hàng rỗng
        setError("Định dạng dữ liệu giỏ hàng không đúng.");
      }
    } catch (err) {
      console.error("Failed to fetch cart data:", err);
      setError(err.message || "Không thể tải dữ liệu giỏ hàng.");
      setCartItems([]); // Reset giỏ hàng khi có lỗi
    } finally {
      setIsLoading(false);
    }
  }, []); // Dependency array rỗng vì hàm này không phụ thuộc props hay state khác (chỉ dùng hằng số và state setters)

  // 2. useEffect gọi fetchCartData khi mount và khi fetchCartData thay đổi (chỉ 1 lần vì useCallback)
  useEffect(() => {
    fetchCartData();
  }, [fetchCartData]);

  // 3. handleResetCart chỉ cần gọi lại fetchCartData
  const handleResetCart = () => {
    // Không cần set isLoading/error ở đây vì fetchCartData đã làm
    console.log("Resetting cart view by refetching data...");
    fetchCartData();
  };

  return (
    <div className="cart-container">
      {/* <h2>Giỏ Hàng (User ID: {USER_ID})</h2> Thêm tiêu đề cho rõ */}
      {isLoading && <div className="loading-cart">Đang tải giỏ hàng...</div>}
      {error && <div className="error-cart">Lỗi: {error}</div>}
      {!isLoading && !error && (
        <>
          {cartItems.length > 0 ? (
            <table className="cart-table">
              <thead>
                <tr>
                  <th>STT</th>
                  <th>Tên Sản Phẩm</th>
                  <th>Số Lượng</th>
                  <th>Đơn Giá</th>
                </tr>
              </thead>
              <tbody>
                {cartItems.map((item) => ( // Không cần index nếu có item.id
                  // Sử dụng ID duy nhất từ item làm key
                  <tr key={item.id}>
                    <td>{item.stt}</td>
                    <td>{item.ten}</td>
                    <td className="number">{item.so_luong}</td>
                    <td className="number">
                      {/* Kiểm tra kiểu dữ liệu trước khi format */}
                      {typeof item.don_gia === 'number'
                        ? item.don_gia.toLocaleString('vi-VN', { style: 'currency', currency: 'VND' })
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-cart">Giỏ hàng trống.</div>
          )}
           {/* Đặt nút Reset bên ngoài bảng */}
           <button onClick={handleResetCart} disabled={isLoading} className="reset-button">
             {isLoading ? 'Đang làm mới...' : 'Làm mới giỏ hàng'} {/* Thay đổi text nút */}
           </button>
        </>
      )}
    </div>
  );
}

export default Cart;