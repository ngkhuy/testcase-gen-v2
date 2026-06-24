import os
import re
import logging
import urllib.request
import markdown
from xhtml2pdf import pisa
from ..core.config import settings

logger = logging.getLogger(__name__)

def check_and_download_fonts():
    """
    Tự động kiểm tra và tải font Roboto hỗ trợ hiển thị Tiếng Việt
    từ Google Fonts về thư mục storage/fonts nếu chưa tồn tại.
    """
    # Thư mục fonts nằm trong storage/fonts
    storage_dir = os.path.dirname(settings.SPEC_DIR)
    font_dir = os.path.join(storage_dir, "fonts")
    os.makedirs(font_dir, exist_ok=True)
    
    regular_path = os.path.join(font_dir, "Roboto-Regular.ttf")
    bold_path = os.path.join(font_dir, "Roboto-Bold.ttf")
    
    urls = {
        regular_path: "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Regular.ttf",
        bold_path: "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Bold.ttf"
    }
    
    for path, url in urls.items():
        if not os.path.exists(path):
            logger.info(f"Đang tải font từ {url} về {path}...")
            try:
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AntigravityPDFGenerator/1.0'}
                )
                with urllib.request.urlopen(req, timeout=15) as response, open(path, 'wb') as out_file:
                    out_file.write(response.read())
                logger.info(f"Đã tải thành công font: {os.path.basename(path)}")
            except Exception as e:
                logger.error(f"Lỗi khi tải font {url}: {e}")
                
    return font_dir, regular_path, bold_path

def parse_markdown_metadata(content: str):
    """
    Trích xuất tiêu đề và thông tin Metadata (Version, Status, Date, Author)
    ở phần đầu của file spec Markdown để dùng cho trang bìa.
    """
    lines = content.split('\n')
    title = "Đặc Tả Kỹ Thuật"
    metadata = {
        "Version": "1.0",
        "Status": "Draft",
        "Date": "",
        "Author": "AI Testcase Generator"
    }
    
    # Tìm tiêu đề H1 đầu tiên
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break
            
    # Regex parse metadata dạng **Key:** Value
    for line in lines:
        # Nếu đã đi qua phần metadata cơ bản (gặp tiêu đề phần tiếp theo hoặc kẻ ngang)
        if line.startswith('---') or line.startswith('## '):
            # Tuy nhiên ta cứ quét hết file cho chắc chắn
            pass
            
        v_match = re.search(r'\*\*Version:\*\*\s*(.*)', line, re.IGNORECASE)
        if v_match:
            metadata["Version"] = v_match.group(1).strip()
            continue
            
        s_match = re.search(r'\*\*Status:\*\*\s*(.*)', line, re.IGNORECASE)
        if s_match:
            metadata["Status"] = s_match.group(1).strip()
            continue
            
        d_match = re.search(r'\*\*Date:\*\*\s*(.*)', line, re.IGNORECASE)
        if d_match:
            metadata["Date"] = d_match.group(1).strip()
            continue
            
        a_match = re.search(r'\*\*Author:\*\*\s*(.*)', line, re.IGNORECASE)
        if a_match:
            metadata["Author"] = a_match.group(1).strip()
            continue
            
    return title, metadata

class PDFGenerator:
    """
    Service chịu trách nhiệm chuyển đổi file Spec Markdown sang file PDF
    định dạng đẹp mắt, hỗ trợ đầy đủ tiếng Việt.
    """
    
    @staticmethod
    def generate_pdf_from_md(md_path: str, pdf_path: str = None):
        try:
            if not os.path.exists(md_path):
                raise FileNotFoundError(f"Không tìm thấy file spec Markdown: {md_path}")
            
            logger.info(f"Bắt đầu sinh PDF từ: {md_path}")
            
            # 1. Đọc nội dung file Markdown
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
                
            # 2. Đảm bảo font Roboto tiếng Việt có sẵn
            font_dir, regular_font, bold_font = check_and_download_fonts()
            
            # Chuẩn hóa đường dẫn font cho CSS của xhtml2pdf (dùng dấu gạch xuôi)
            regular_font_css = regular_font.replace('\\', '/')
            bold_font_css = bold_font.replace('\\', '/')
            
            # 3. Phân tích metadata và loại bỏ tiêu đề đầu tiên và metadata thô để không lặp lại trong nội dung
            title, metadata = parse_markdown_metadata(md_content)
            
            # Làm sạch nội dung Markdown để hiển thị phần thân
            # Ta bỏ qua tiêu đề H1 đầu tiên và phần metadata nằm giữa dòng đầu và dòng kẻ ngang "---"
            cleaned_lines = []
            skip_header = True
            lines = md_content.split('\n')
            
            # Bỏ qua phần đầu (H1 và các dòng metadata đầu tiên cho đến khi gặp kẻ ngang --- thứ nhất)
            hr_count = 0
            for line in lines:
                if line.startswith('# ') and skip_header:
                    continue
                if line.startswith('**Version:**') or line.startswith('**Status:**') or line.startswith('**Date:**') or line.startswith('**Author:**'):
                    continue
                if line.strip() == '---' and hr_count < 1 and skip_header:
                    hr_count += 1
                    # Kết thúc phần skip header
                    skip_header = False
                    continue
                cleaned_lines.append(line)
                
            body_md = '\n'.join(cleaned_lines)
            
            # 4. Chuyển đổi Markdown sang HTML (hỗ trợ tables, fenced_code để hiển thị tốt bảng biểu)
            body_html = markdown.markdown(
                body_md, 
                extensions=['tables', 'fenced_code']
            )
            
            # 5. Xây dựng CSS phong cách premium
            css_styles = f"""
            @font-face {{
                font-family: 'Roboto';
                src: url('{regular_font_css}');
            }}
            @font-face {{
                font-family: 'Roboto';
                src: url('{bold_font_css}');
                font-weight: bold;
            }}
            
            @page {{
                size: a4;
                margin: 2.5cm 2cm 2.5cm 2cm;
                @frame header_frame {{
                    -pdf-frame-content: header_content;
                    left: 2cm;
                    width: 17cm;
                    top: 1cm;
                    height: 1.2cm;
                }}
                @frame footer_frame {{
                    -pdf-frame-content: footer_content;
                    left: 2cm;
                    width: 17cm;
                    top: 27.2cm;
                    height: 1.2cm;
                }}
            }}
            
            body {{
                font-family: 'Roboto', sans-serif;
                font-size: 10.5pt;
                line-height: 1.6;
                color: #1f2937;
            }}
            
            h1, h2, h3, h4 {{
                font-family: 'Roboto', sans-serif;
                font-weight: bold;
                color: #111827;
            }}
            
            h1 {{
                font-size: 20pt;
                margin-top: 0;
                margin-bottom: 15px;
                color: #5b21b6;
                border-bottom: 2px solid #8b5cf6;
                padding-bottom: 8px;
            }}
            
            h2 {{
                font-size: 14pt;
                color: #1e1b4b;
                margin-top: 25px;
                margin-bottom: 12px;
                border-left: 4px solid #8b5cf6;
                padding-left: 8px;
            }}
            
            h3 {{
                font-size: 12pt;
                color: #3730a3;
                margin-top: 18px;
                margin-bottom: 8px;
            }}
            
            h4 {{
                font-size: 11pt;
                color: #1f2937;
                margin-top: 12px;
                margin-bottom: 6px;
            }}
            
            p {{
                margin-bottom: 10px;
                text-align: justify;
            }}
            
            ul, ol {{
                margin-left: 20px;
                margin-bottom: 12px;
            }}
            
            li {{
                margin-bottom: 5px;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                margin-bottom: 15px;
            }}
            
            th, td {{
                padding: 8px 10px;
                border: 1px solid #cbd5e1;
                font-size: 9.5pt;
                text-align: left;
                vertical-align: top;
            }}
            
            th {{
                background-color: #f1f5f9;
                font-weight: bold;
                color: #0f172a;
            }}
            
            tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
            
            blockquote {{
                border-left: 4px solid #8b5cf6;
                background-color: #f5f3ff;
                padding: 8px 15px;
                margin-top: 12px;
                margin-bottom: 12px;
                font-style: italic;
                color: #4b5563;
            }}
            
            pre {{
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-left: 4px solid #06b6d4;
                padding: 10px;
                margin-top: 15px;
                margin-bottom: 15px;
                font-size: 9pt;
            }}
            
            code {{
                font-size: 9pt;
                background-color: #f1f5f9;
                padding: 2px 4px;
            }}
            
            hr {{
                border: 0;
                border-top: 1px solid #e2e8f0;
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            
            /* Cover page styling */
            .cover-page {{
                text-align: center;
                padding-top: 4cm;
            }}
            
            .cover-title {{
                font-size: 24pt;
                line-height: 1.3;
                color: #5b21b6;
                margin-bottom: 20px;
                font-weight: bold;
            }}
            
            .cover-subtitle {{
                font-size: 14pt;
                color: #6b7280;
                margin-bottom: 4cm;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
            
            .cover-meta {{
                width: 70%;
                margin: 0 auto;
            }}
            
            .cover-meta-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 0 auto;
            }}
            
            .cover-meta-table td {{
                padding: 8px;
                border: none;
                font-size: 11pt;
            }}
            
            .cover-meta-table td.label {{
                text-align: right;
                font-weight: bold;
                color: #4b5563;
                width: 40%;
            }}
            
            .cover-meta-table td.value {{
                text-align: left;
                color: #1f2937;
                width: 60%;
            }}
            
            .cover-meta-table tr {{
                background-color: transparent !important;
            }}
            
            #header_content {{
                font-size: 8.5pt;
                color: #9ca3af;
                text-align: right;
                border-bottom: 1px solid #e5e7eb;
                padding-bottom: 5px;
            }}
            
            #footer_content {{
                font-size: 8.5pt;
                color: #9ca3af;
                border-top: 1px solid #e5e7eb;
                padding-top: 5px;
            }}
            """
            
            # 6. Thiết lập khung HTML hoàn chỉnh bao gồm trang bìa và Header/Footer
            html_document = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    {css_styles}
                </style>
            </head>
            <body>
                <!-- Header và Footer templates cho xhtml2pdf -->
                <div id="header_content">Tài Liệu Đặc Tả Kỹ Thuật (Technical Specification)</div>
                <div id="footer_content">
                    <table style="width: 100%; border: 0; margin: 0; padding: 0;">
                        <tr style="background-color: transparent;">
                            <td style="border: 0; text-align: left; color: #9ca3af; padding: 0; font-size: 8.5pt;">Hệ Thống AI Testcase Generator</td>
                            <td style="border: 0; text-align: right; color: #9ca3af; padding: 0; font-size: 8.5pt;">Trang <pdf:pagenumber/> / <pdf:pagecount/></td>
                        </tr>
                    </table>
                </div>

                <!-- Trang Bìa (Cover Page) -->
                <div class="cover-page">
                    <div class="cover-title">{title}</div>
                    <div class="cover-subtitle">Đặc Tả Yêu Cầu Kỹ Thuật</div>
                    
                    <div class="cover-meta">
                        <table class="cover-meta-table">
                            <tr style="background-color: transparent;">
                                <td class="label">Phiên bản:</td>
                                <td class="value">{metadata.get('Version', '1.0')}</td>
                            </tr>
                            <tr style="background-color: transparent;">
                                <td class="label">Trạng thái:</td>
                                <td class="value">{metadata.get('Status', 'Draft')}</td>
                            </tr>
                            <tr style="background-color: transparent;">
                                <td class="label">Ngày tạo:</td>
                                <td class="value">{metadata.get('Date', '-')}</td>
                            </tr>
                            <tr style="background-color: transparent;">
                                <td class="label">Tác giả:</td>
                                <td class="value">{metadata.get('Author', 'AI Generator')}</td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <!-- Ngắt trang bắt đầu nội dung chính -->
                <div style="page-break-after: always; clear: both;"></div>
                
                <!-- Nội dung chính của Spec -->
                <div class="content-body">
                    <h1>{title}</h1>
                    {body_html}
                </div>
            </body>
            </html>
            """
            
            # 7. Biên dịch sang PDF
            import io
            pdf_buffer = io.BytesIO()
            pisa_status = pisa.CreatePDF(
                html_document,
                dest=pdf_buffer
            )
            
            if pisa_status.err:
                logger.error(f"Lỗi chuyển đổi PDF từ xhtml2pdf: {pisa_status.err}")
                pdf_buffer.close()
                return None
                
            pdf_data = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            if pdf_path:
                os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
                with open(pdf_path, "wb") as result_file:
                    result_file.write(pdf_data)
                logger.info(f"Đã tạo thành công file PDF tại: {pdf_path}")
                
            return pdf_data
            
        except Exception as e:
            logger.error(f"Lỗi hệ thống khi sinh PDF: {e}", exc_info=True)
            return None
