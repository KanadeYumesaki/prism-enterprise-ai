import io
from fastapi import UploadFile
from pypdf import PdfReader

# [NEW CODE] なぜこの関数が必要か:
# アップロードされたファイル (PDFやテキスト) から、LLMが理解できる「テキストデータ」を取り出すためです。
async def extract_text_from_file(file: UploadFile) -> str:
    """
    アップロードされたファイルからテキストを抽出する関数です。
    対応形式: PDF, Text
    """
    
    # [NEW CODE] ファイル名がない場合は空文字を返して終了します
    if not file.filename:
        return ""

    # [NEW CODE] ファイルの中身を非同期で読み込みます (バイト列として取得)
    # awaitを使うことで、読み込み中に他の処理をブロックしません
    content = await file.read()

    # [NEW CODE] ファイル名の末尾(拡張子)を見て処理を分岐します
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        # [NEW CODE] PDFファイルの処理:
        # pypdfのPdfReaderを使って、バイト列からPDFを読み込みます
        # io.BytesIOは、メモリ上のバイト列をファイルのように扱うためのクラスです
        reader = PdfReader(io.BytesIO(content))
        text = ""
        
        # [NEW CODE] 全ページをループしてテキストを抽出・結合します
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text

    else:
        # [NEW CODE] その他のファイル(主にテキスト)の処理:
        # 単純にバイト列をUTF-8文字列に変換します
        # errors="ignore" は、変換できない文字があってもエラーにせず無視する設定です
        return content.decode("utf-8", errors="ignore")
