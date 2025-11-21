# exception_tracker.py
import sys
import traceback
from functools import wraps
import logging
import inspect

# ロガーの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

def trace_exceptions(func):
    """
    関数内で発生した例外の詳細な情報を出力するデコレータ
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            
            # スタックトレース情報の取得
            stack_trace = traceback.extract_tb(exc_traceback)
            
            # 現在の関数のフレーム情報を取得
            current_frame = inspect.currentframe()
            caller_frame = current_frame.f_back
            
            # エラー情報の出力
            logger.error(f"\n{'=' * 50}")
            logger.error(f"例外が発生した関数: {func.__name__}")
            logger.error(f"例外の種類: {exc_type.__name__}")
            logger.error(f"例外メッセージ: {str(e)}")
            logger.error("\nスタックトレース:")
            
            for filename, line_num, func_name, text in stack_trace:
                logger.error(f"  ファイル '{filename}', {line_num}行目")
                logger.error(f"  関数名: {func_name}")
                if text:
                    logger.error(f"  実行コード: {text}\n")
            
            logger.error('=' * 50)
            raise  # 元の例外を再度発生させる
            
    return wrapper