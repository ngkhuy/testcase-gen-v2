from bs4 import BeautifulSoup

def transform_tables(markdown_content):
    soup = BeautifulSoup(markdown_content, "html.parser")
    
    # Tìm tất cả các thẻ table
    for table in soup.find_all("table"):
        markdown_table = []
        rows = table.find_all("tr")
        
        for i, row in enumerate(rows):
            # Lấy nội dung th, td
            cols = row.find_all(["th", "td"])
            cols_text = [c.get_text(strip=True) for c in cols]
            
            # Tạo dòng markdown
            markdown_table.append("| " + " | ".join(cols_text) + " |")
            
            # Nếu là dòng header (dòng đầu tiên), thêm dòng phân cách ---
            if i == 0:
                separator = "| " + " | ".join(["---"] * len(cols)) + " |"
                markdown_table.append(separator)
        
        # Thay thế thẻ table bằng chuỗi markdown table vừa tạo
        table.replace_with("\n" + "\n".join(markdown_table) + "\n")
    
    return str(soup)