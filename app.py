import streamlit as st
import database as db
import pandas as pd
from datetime import datetime, timedelta

# 老闆密碼
BOSS_PASSWORD = "123456"

# 初始化資料庫
db.init_db()

# 頁面設定
st.set_page_config(page_title="團購訂單系統", layout="wide")

st.title("團購訂單系統")

# 初始化 session state
if "boss_authenticated" not in st.session_state:
    st.session_state.boss_authenticated = False
if "new_items" not in st.session_state:
    st.session_state.new_items = []
if "editing_order_id" not in st.session_state:
    st.session_state.editing_order_id = None
if "editing_group_order_id" not in st.session_state:
    st.session_state.editing_group_order_id = None
if "edit_items" not in st.session_state:
    st.session_state.edit_items = []

# 側邊欄 - 角色選擇
role = st.sidebar.radio("選擇功能", ["商品訂購", "管理後台"])

# 老闆登出按鈕
if role == "管理後台" and st.session_state.boss_authenticated:
    if st.sidebar.button("登出"):
        st.session_state.boss_authenticated = False
        st.rerun()

# ============================================
# 老闆介面
# ============================================
if role == "管理後台":
    st.header("管理後台")
    
    # 密碼驗證
    if not st.session_state.boss_authenticated:
        st.warning("請輸入密碼以進入管理後台")
        
        password = st.text_input("密碼", type="password", placeholder="請輸入密碼")
        
        if st.button("登入", type="primary"):
            if password == BOSS_PASSWORD:
                st.session_state.boss_authenticated = True
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("密碼錯誤")
        
        st.stop()
    
    tab1, tab2, tab3 = st.tabs(["建立團購單", "管理團購單", "訂單統計"])
    
    # ---- 建立團購單 ----
    with tab1:
        st.subheader("建立新團購單")
        
        # 團購單基本資訊
        title = st.text_input("團購單名稱", placeholder="例如：1月份飲料團購", key="new_order_title")
        description = st.text_area("說明", placeholder="例如：預計1/20截止，1/25到貨", key="new_order_desc")
        
        # 時間設定
        st.write("**開放時間設定**")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("開始日期", value=datetime.now().date(), key="start_date")
        with col2:
            end_date = st.date_input("結束日期", value=(datetime.now() + timedelta(days=7)).date(), key="end_date")
        
        st.divider()
        
        # 新增品項區域
        st.subheader("新增品項")
        col1, col2 = st.columns([3, 2])
        with col1:
            item_name = st.text_input("品項名稱", placeholder="例如：海帶", key="new_item_name")
        with col2:
            item_price = st.number_input("價格", min_value=0.0, step=5.0, key="new_item_price")
        
        if st.button("加入品項"):
            if item_name and item_price > 0:
                st.session_state.new_items.append({"name": item_name, "price": item_price})
                del st.session_state["new_item_name"]
                del st.session_state["new_item_price"]
                st.rerun()
            else:
                st.error("請填寫品項名稱和價格")
        
        # 顯示已加入的品項
        if st.session_state.new_items:
            st.write("**已加入的品項：**")
            for idx, item in enumerate(st.session_state.new_items):
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.write(item['name'])
                col2.write(f"${item['price']}")
                if col3.button("刪除", key=f"del_new_item_{idx}"):
                    st.session_state.new_items.pop(idx)
                    st.rerun()
        
        st.divider()
        
        # 建立團購單按鈕
        if st.button("建立團購單", type="primary"):
            if not title:
                st.error("請輸入團購單名稱")
            elif not st.session_state.new_items:
                st.error("請至少新增一個品項")
            else:
                start_datetime = start_date.strftime("%Y-%m-%d")
                end_datetime = end_date.strftime("%Y-%m-%d")
                order_id = db.create_group_order(title, description, start_datetime, end_datetime)
                for item in st.session_state.new_items:
                    db.add_item(order_id, item['name'], item['price'])
                st.session_state.new_items = []
                st.success(f"團購單「{title}」建立成功！")
                st.rerun()
    
    # ---- 管理團購單 ----
    with tab2:
        st.subheader("團購單列表")
        
        group_orders = db.get_all_group_orders()
        
        if group_orders:
            # 分開開放中和已關閉的訂單
            open_orders = [o for o in group_orders if o['status'] == 'open']
            closed_orders = [o for o in group_orders if o['status'] == 'closed']
            
            # 開放中的訂單
            with st.expander(f"開放中 ({len(open_orders)})", expanded=True):
                if open_orders:
                    for order in open_orders:
                        with st.container(border=True):
                            # 檢查是否正在編輯此團購單
                            if st.session_state.editing_group_order_id == order['id']:
                                # 編輯模式
                                edit_title = st.text_input("團購單名稱", value=order['title'], key=f"edit_title_{order['id']}")
                                edit_desc = st.text_area("說明", value=order['description'] or "", key=f"edit_desc_{order['id']}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    edit_start = st.date_input("開始日期", 
                                        value=datetime.strptime(order['start_time'], "%Y-%m-%d").date() if order['start_time'] else datetime.now().date(),
                                        key=f"edit_start_{order['id']}")
                                with col2:
                                    edit_end = st.date_input("結束日期",
                                        value=datetime.strptime(order['end_time'], "%Y-%m-%d").date() if order['end_time'] else datetime.now().date(),
                                        key=f"edit_end_{order['id']}")
                                
                                # 品項編輯
                                st.write("**品項管理**")
                                items = db.get_items_by_group_order(order['id'])
                                for item in items:
                                    col1, col2, col3 = st.columns([3, 2, 1])
                                    col1.write(item['name'])
                                    col2.write(f"${item['price']}")
                                    if col3.button("刪除", key=f"del_item_{order['id']}_{item['id']}"):
                                        db.delete_item(item['id'])
                                        st.rerun()
                                
                                # 新增品項
                                st.write("**新增品項**")
                                col1, col2 = st.columns([3, 2])
                                with col1:
                                    new_item_name = st.text_input("品項名稱", key=f"new_item_name_{order['id']}")
                                with col2:
                                    new_item_price = st.number_input("價格", min_value=0.0, step=5.0, key=f"new_item_price_{order['id']}")
                                if st.button("加入品項", key=f"add_item_{order['id']}"):
                                    if new_item_name and new_item_price > 0:
                                        db.add_item(order['id'], new_item_name, new_item_price)
                                        del st.session_state[f"new_item_name_{order['id']}"]
                                        del st.session_state[f"new_item_price_{order['id']}"]
                                        st.rerun()
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("儲存修改", key=f"save_group_{order['id']}", type="primary"):
                                        db.update_group_order(order['id'], edit_title, edit_desc, 
                                            edit_start.strftime("%Y-%m-%d"), edit_end.strftime("%Y-%m-%d"))
                                        st.session_state.editing_group_order_id = None
                                        st.success("團購單已更新！")
                                        st.rerun()
                                with col2:
                                    if st.button("取消", key=f"cancel_group_{order['id']}"):
                                        st.session_state.editing_group_order_id = None
                                        st.rerun()
                            else:
                                # 顯示模式
                                st.write(f"**{order['title']}**")
                                st.write(f"說明：{order['description'] or '無'}")
                                st.write(f"開放時間：{order['start_time'] or '無'} ~ {order['end_time'] or '無'}")
                                
                                # 品項列表
                                items = db.get_items_by_group_order(order['id'])
                                if items:
                                    items_df = pd.DataFrame([dict(i) for i in items])[['name', 'price']]
                                    items_df.columns = ['品項', '價格']
                                    items_df.index = items_df.index + 1
                                    st.dataframe(items_df, use_container_width=True)
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    if st.button("編輯", key=f"edit_group_{order['id']}"):
                                        st.session_state.editing_group_order_id = order['id']
                                        st.rerun()
                                with col2:
                                    if st.button("關閉團購", key=f"close_{order['id']}"):
                                        db.update_group_order_status(order['id'], 'closed')
                                        st.rerun()
                                with col3:
                                    if st.button("刪除", key=f"del_{order['id']}", type="secondary"):
                                        db.delete_group_order(order['id'])
                                        st.rerun()
                else:
                    st.info("目前沒有開放中的團購單")
            
            # 已關閉的訂單
            with st.expander(f"已關閉 ({len(closed_orders)})", expanded=False):
                if closed_orders:
                    for order in closed_orders:
                        with st.container(border=True):
                            # 檢查是否正在編輯此團購單
                            if st.session_state.editing_group_order_id == order['id']:
                                # 編輯模式
                                edit_title = st.text_input("團購單名稱", value=order['title'], key=f"edit_title_c_{order['id']}")
                                edit_desc = st.text_area("說明", value=order['description'] or "", key=f"edit_desc_c_{order['id']}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    edit_start = st.date_input("開始日期", 
                                        value=datetime.strptime(order['start_time'], "%Y-%m-%d").date() if order['start_time'] else datetime.now().date(),
                                        key=f"edit_start_c_{order['id']}")
                                with col2:
                                    edit_end = st.date_input("結束日期",
                                        value=datetime.strptime(order['end_time'], "%Y-%m-%d").date() if order['end_time'] else datetime.now().date(),
                                        key=f"edit_end_c_{order['id']}")
                                
                                # 品項編輯
                                st.write("**品項管理**")
                                items = db.get_items_by_group_order(order['id'])
                                for item in items:
                                    col1, col2, col3 = st.columns([3, 2, 1])
                                    col1.write(item['name'])
                                    col2.write(f"${item['price']}")
                                    if col3.button("刪除", key=f"del_item_c_{order['id']}_{item['id']}"):
                                        db.delete_item(item['id'])
                                        st.rerun()
                                
                                # 新增品項
                                st.write("**新增品項**")
                                col1, col2 = st.columns([3, 2])
                                with col1:
                                    new_item_name = st.text_input("品項名稱", key=f"new_item_name_c_{order['id']}")
                                with col2:
                                    new_item_price = st.number_input("價格", min_value=0.0, step=5.0, key=f"new_item_price_c_{order['id']}")
                                if st.button("加入品項", key=f"add_item_c_{order['id']}"):
                                    if new_item_name and new_item_price > 0:
                                        db.add_item(order['id'], new_item_name, new_item_price)
                                        del st.session_state[f"new_item_name_c_{order['id']}"]
                                        del st.session_state[f"new_item_price_c_{order['id']}"]
                                        st.rerun()
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("儲存修改", key=f"save_group_c_{order['id']}", type="primary"):
                                        db.update_group_order(order['id'], edit_title, edit_desc, 
                                            edit_start.strftime("%Y-%m-%d"), edit_end.strftime("%Y-%m-%d"))
                                        st.session_state.editing_group_order_id = None
                                        st.success("團購單已更新！")
                                        st.rerun()
                                with col2:
                                    if st.button("取消", key=f"cancel_group_c_{order['id']}"):
                                        st.session_state.editing_group_order_id = None
                                        st.rerun()
                            else:
                                # 顯示模式
                                st.write(f"**{order['title']}**")
                                st.write(f"說明：{order['description'] or '無'}")
                                st.write(f"開放時間：{order['start_time'] or '無'} ~ {order['end_time'] or '無'}")
                                
                                # 品項列表
                                items = db.get_items_by_group_order(order['id'])
                                if items:
                                    items_df = pd.DataFrame([dict(i) for i in items])[['name', 'price']]
                                    items_df.columns = ['品項', '價格']
                                    items_df.index = items_df.index + 1
                                    st.dataframe(items_df, use_container_width=True)
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    if st.button("編輯", key=f"edit_group_c_{order['id']}"):
                                        st.session_state.editing_group_order_id = order['id']
                                        st.rerun()
                                with col2:
                                    if st.button("重新開放", key=f"open_{order['id']}"):
                                        db.update_group_order_status(order['id'], 'open')
                                        st.rerun()
                                with col3:
                                    if st.button("刪除", key=f"del_closed_{order['id']}", type="secondary"):
                                        db.delete_group_order(order['id'])
                                        st.rerun()
                else:
                    st.info("目前沒有已關閉的團購單")
        else:
            st.info("尚無團購單")
    
    # ---- 訂單統計 ----
    with tab3:
        st.subheader("訂單統計")
        
        group_orders = db.get_all_group_orders()
        
        if group_orders:
            order_options = {o['title']: o['id'] for o in group_orders}
            selected_order = st.selectbox("選擇團購單", options=list(order_options.keys()), key="stats_order")
            
            if selected_order:
                order_id = order_options[selected_order]
                
                # 品項彙總
                st.write("### 品項彙總")
                summary = db.get_group_order_summary(order_id)
                if summary:
                    summary_df = pd.DataFrame([dict(s) for s in summary])[['name', 'price', 'total_qty', 'total_amount']]
                    summary_df.columns = ['品項', '單價', '總數量', '總金額']
                    summary_df.index = summary_df.index + 1
                    st.dataframe(summary_df, use_container_width=True)
                    
                    total = sum(s['total_amount'] for s in summary)
                    st.metric("總金額", f"${total:,.0f}")
                    
                    # 產生詳細明細 CSV
                    detail_rows = []
                    for s in summary:
                        buyers = db.get_item_buyers(s['id'])
                        if buyers:
                            for b in buyers:
                                detail_rows.append({
                                    '品項': s['name'],
                                    '單價': s['price'],
                                    '顧客姓名': b['customer_name'],
                                    '數量': b['quantity'],
                                    '小計': b['subtotal']
                                })
                        else:
                            detail_rows.append({
                                '品項': s['name'],
                                '單價': s['price'],
                                '顧客姓名': '',
                                '數量': 0,
                                '小計': 0
                            })
                    
                    detail_df = pd.DataFrame(detail_rows)
                    detail_df.index = detail_df.index + 1
                    # 使用 BOM 確保 Excel 正確顯示中文
                    csv_buffer = '\ufeff' + detail_df.to_csv(index=True, encoding='utf-8')
                    st.download_button(
                        label="下載訂單明細 CSV",
                        data=csv_buffer.encode('utf-8'),
                        file_name=f"{selected_order}_訂單明細.csv",
                        mime="text/csv"
                    )
                
                # 按品項展開購買者
                st.write("### 品項購買明細")
                for s in summary:
                    with st.expander(f"{s['name']} - 共 {int(s['total_qty'])} 份"):
                        buyers = db.get_item_buyers(s['id'])
                        if buyers:
                            buyers_df = pd.DataFrame([dict(b) for b in buyers])
                            buyers_df.columns = ['顧客姓名', '數量', '小計']
                            buyers_df.index = buyers_df.index + 1
                            st.dataframe(buyers_df, use_container_width=True)
                        else:
                            st.info("尚無人購買此品項")
                
                # 顧客訂單列表
                st.write("### 顧客訂單")
                customer_orders = db.get_customer_orders_by_group(order_id)
                
                if customer_orders:
                    for co in customer_orders:
                        with st.expander(f"{co['customer_name']} - ${co['total_amount'] or 0:,.0f}"):
                            # 檢查是否正在編輯此訂單
                            if st.session_state.editing_order_id == co['id']:
                                # 編輯模式
                                items = db.get_items_by_group_order(order_id)
                                current_details = db.get_order_details_as_dict(co['id'])
                                
                                edit_quantities = {}
                                edit_total = 0
                                for item in items:
                                    col1, col2, col3 = st.columns([3, 2, 2])
                                    with col1:
                                        st.write(f"**{item['name']}**")
                                    with col2:
                                        st.write(f"${item['price']}")
                                    with col3:
                                        qty = st.number_input(
                                            "數量",
                                            min_value=0,
                                            max_value=99,
                                            value=current_details.get(item['id'], 0),
                                            key=f"edit_qty_{co['id']}_{item['id']}",
                                            label_visibility="collapsed"
                                        )
                                        edit_quantities[item['id']] = qty
                                        edit_total += qty * item['price']
                                
                                st.metric("訂單總計", f"${edit_total:,.0f}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("儲存修改", key=f"save_edit_{co['id']}", type="primary"):
                                        db.update_customer_order(co['id'], edit_quantities)
                                        st.session_state.editing_order_id = None
                                        st.success("訂單已更新！")
                                        st.rerun()
                                with col2:
                                    if st.button("取消", key=f"cancel_edit_{co['id']}"):
                                        st.session_state.editing_order_id = None
                                        st.rerun()
                            else:
                                # 顯示模式
                                details = db.get_order_details(co['id'])
                                if details:
                                    details_df = pd.DataFrame([dict(d) for d in details])[['name', 'quantity', 'price', 'subtotal']]
                                    details_df.columns = ['品項', '數量', '單價', '小計']
                                    details_df.index = details_df.index + 1
                                    st.dataframe(details_df, use_container_width=True)
                                
                                btn_col1, btn_col2, _ = st.columns([1, 1, 3])
                                with btn_col1:
                                    if st.button("修改訂單", key=f"edit_co_{co['id']}"):
                                        st.session_state.editing_order_id = co['id']
                                        st.rerun()
                                with btn_col2:
                                    if st.button("刪除此訂單", key=f"del_co_{co['id']}"):
                                        db.delete_customer_order(co['id'])
                                        st.rerun()
                else:
                    st.info("尚無顧客訂單")
        else:
            st.info("尚無團購單")

# ============================================
# 顧客介面
# ============================================
else:
    st.header("商品訂購")
    
    # 功能選擇
    customer_tab1, customer_tab2 = st.tabs(["新增訂單", "修改訂單"])
    
    with customer_tab1:
        open_orders = db.get_open_group_orders()
        
        if open_orders:
            # 選擇團購單
            order_options = {o['title']: o['id'] for o in open_orders}
            selected_order = st.selectbox("選擇團購單", options=list(order_options.keys()), key="new_order_select")
            
            if selected_order:
                order_id = order_options[selected_order]
                
                # 找出對應的訂單資訊
                order_info = next(o for o in open_orders if o['id'] == order_id)
                if order_info['description']:
                    st.info(order_info['description'])
                
                # 顯示開放時間
                if order_info['end_time']:
                    st.write(f"**截止時間：{order_info['end_time']}**")
                
                items = db.get_items_by_group_order(order_id)
                
                if items:
                    st.subheader("選擇商品")
                    
                    customer_name = st.text_input("您的姓名", placeholder="請輸入姓名", key="new_customer_name")
                    
                    st.divider()
                    
                    # 商品選擇
                    quantities = {}
                    total = 0
                    
                    for item in items:
                        col1, col2, col3 = st.columns([3, 2, 2])
                        with col1:
                            st.write(f"**{item['name']}**")
                        with col2:
                            st.write(f"${item['price']}")
                        with col3:
                            qty = st.number_input(
                                "數量",
                                min_value=0,
                                max_value=99,
                                value=0,
                                key=f"qty_{item['id']}",
                                label_visibility="collapsed"
                            )
                            quantities[item['id']] = qty
                            total += qty * item['price']
                    
                    st.divider()
                    
                    # 顯示總計
                    st.metric("訂單總計", f"${total:,.0f}")
                    
                    # 送出訂單
                    if st.button("送出訂單", type="primary", use_container_width=True):
                        if not customer_name:
                            st.error("請輸入您的姓名")
                        elif total == 0:
                            st.error("請至少選擇一項商品")
                        else:
                            db.create_customer_order(order_id, customer_name, quantities)
                            st.success("訂單送出成功！")
                            st.balloons()
                else:
                    st.warning("此團購單尚無品項")
        else:
            st.info("目前沒有開放中的團購單")
    
    with customer_tab2:
        st.subheader("查詢並修改訂單")
        
        open_orders = db.get_open_group_orders()
        
        if open_orders:
            order_options = {o['title']: o['id'] for o in open_orders}
            selected_order = st.selectbox("選擇團購單", options=list(order_options.keys()), key="edit_order_select")
            
            if selected_order:
                order_id = order_options[selected_order]
                
                search_name = st.text_input("輸入您的姓名查詢訂單", placeholder="請輸入姓名", key="search_name")
                
                if search_name:
                    my_orders = db.get_customer_orders_by_name(order_id, search_name)
                    
                    if my_orders:
                        st.write(f"找到 {len(my_orders)} 筆訂單")
                        
                        for order in my_orders:
                            with st.expander(f"訂單 #{order['id']} - ${order['total_amount'] or 0:,.0f}"):
                                if st.session_state.editing_order_id == order['id']:
                                    # 編輯模式
                                    items = db.get_items_by_group_order(order_id)
                                    current_details = db.get_order_details_as_dict(order['id'])
                                    
                                    edit_quantities = {}
                                    edit_total = 0
                                    for item in items:
                                        col1, col2, col3 = st.columns([3, 2, 2])
                                        with col1:
                                            st.write(f"**{item['name']}**")
                                        with col2:
                                            st.write(f"${item['price']}")
                                        with col3:
                                            qty = st.number_input(
                                                "數量",
                                                min_value=0,
                                                max_value=99,
                                                value=current_details.get(item['id'], 0),
                                                key=f"cust_edit_qty_{order['id']}_{item['id']}",
                                                label_visibility="collapsed"
                                            )
                                            edit_quantities[item['id']] = qty
                                            edit_total += qty * item['price']
                                    
                                    st.metric("訂單總計", f"${edit_total:,.0f}")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("儲存修改", key=f"cust_save_{order['id']}", type="primary"):
                                            db.update_customer_order(order['id'], edit_quantities)
                                            st.session_state.editing_order_id = None
                                            st.success("訂單已更新！")
                                            st.rerun()
                                    with col2:
                                        if st.button("取消", key=f"cust_cancel_{order['id']}"):
                                            st.session_state.editing_order_id = None
                                            st.rerun()
                                else:
                                    # 顯示模式
                                    details = db.get_order_details(order['id'])
                                    if details:
                                        details_df = pd.DataFrame([dict(d) for d in details])[['name', 'quantity', 'price', 'subtotal']]
                                        details_df.columns = ['品項', '數量', '單價', '小計']
                                        details_df.index = details_df.index + 1
                                        st.dataframe(details_df, use_container_width=True)
                                    
                                    if st.button("修改此訂單", key=f"cust_edit_{order['id']}"):
                                        st.session_state.editing_order_id = order['id']
                                        st.rerun()
                    else:
                        st.info("查無訂單，請確認姓名是否正確")
        else:
            st.info("目前沒有開放中的團購單")
