#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import os
import logging
from Config import Config as cf
from datetime import datetime
from OnionScraperLib import utilFuncs as uf
from OnionScraperLib import FileOperate as fo
import shutil
import sys

# 既存の関数をインポート
def clean_temp_directory(temp_dir: str, hours: int = 2, max_retries: int = 3) -> tuple[list, list]:
    """
    指定されたテンポラリディレクトリ内の古いファイルとフォルダを削除します。
    Args:
        temp_dir (str): 削除対象のディレクトリパス
        hours (int): 経過時間の閾値（デフォルト：2時間）
        max_retries (int): 削除失敗時の最大リトライ回数（デフォルト：3回）
    Returns:
        tuple[list, list]: (成功したパスのリスト, 失敗したパスのリスト)
    """
    # ログの設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    current_time = time.time()
    threshold = current_time - (hours * 3600)
    
    success_list = []
    failed_list = []
    try:
        # サブフォルダを含むすべてのファイルとディレクトリを走査
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            # まずファイルを処理
            for name in files:
                file_path = os.path.join(root, name)
                try:
                    # ファイルの最終更新時刻を取得
                    mtime = os.path.getmtime(file_path)
                    
                    if mtime < threshold:
                        # 指定時間より古い場合、削除を試みる
                        success = False
                        for attempt in range(max_retries):
                            try:
                                os.remove(file_path)
                                success = True
                                success_list.append(file_path)
                                logging.info(f"ファイルを削除しました: {file_path}")
                                break
                            except Exception as e:
                                if attempt == max_retries - 1:
                                    logging.error(f"ファイルの削除に失敗: {file_path}, エラー: {str(e)}")
                                time.sleep(1)  # 少し待機してから再試行
                        
                        if not success:
                            failed_list.append(file_path)
                
                except Exception as e:
                    logging.error(f"ファイル処理中にエラーが発生: {file_path}, エラー: {str(e)}")
                    failed_list.append(file_path)
            # 次にディレクトリを処理
            for name in dirs:
                dir_path = os.path.join(root, name)
                try:
                    # ディレクトリの最終更新時刻を取得
                    mtime = os.path.getmtime(dir_path)
                    
                    if mtime < threshold:
                        # 指定時間より古い場合、削除を試みる
                        success = False
                        for attempt in range(max_retries):
                            try:
                                shutil.rmtree(dir_path)
                                success = True
                                success_list.append(dir_path)
                                logging.info(f"ディレクトリを削除しました: {dir_path}")
                                break
                            except Exception as e:
                                if attempt == max_retries - 1:
                                    logging.error(f"ディレクトリの削除に失敗: {dir_path}, エラー: {str(e)}")
                                time.sleep(1)  # 少し待機してから再試行
                        
                        if not success:
                            failed_list.append(dir_path)
                except Exception as e:
                    logging.error(f"ディレクトリ処理中にエラーが発生: {dir_path}, エラー: {str(e)}")
                    failed_list.append(dir_path)
    except Exception as e:
        logging.error(f"全体の処理中にエラーが発生: {str(e)}")
    return success_list, failed_list

def main():
    """
    メイン関数: 10分ごとにclean_temp_directory関数を実行します
    """
    # ログの設定
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_cleaner.log')
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # コンソールにもログを出力
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)
    
    logging.info("一時ファイル自動クリーンアップサービスを開始しました")
    
    # テンポラリディレクトリのパスを設定
    try:
        temp_dir = r"C:\Users\malga\AppData\Local\Temp"
        logging.info(f"テンポラリディレクトリパス: {temp_dir}")
        
        # ディレクトリが存在しない場合は作成
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            logging.info(f"テンポラリディレクトリを作成しました: {temp_dir}")
    except Exception as e:
        logging.error(f"設定の読み込みに失敗しました: {str(e)}")
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
        logging.info(f"デフォルトのテンポラリディレクトリを使用します: {temp_dir}")
        
        # デフォルトディレクトリが存在しない場合は作成
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            logging.info(f"デフォルトのテンポラリディレクトリを作成しました: {temp_dir}")
    
    # クリーンアップの間隔（秒）
    cleanup_interval = 10 * 60  # 10分
    
    try:
        # 無限ループで実行
        while True:
            # 現在の実行時間をログに記録
            current_time = datetime.now()
            logging.info(f"===== クリーンアップ処理実行: {current_time.strftime('%Y-%m-%d %H:%M:%S')} =====")
            
            start_time = time.time()
            logging.info("一時ファイルのクリーンアップを開始します...")
            
            # クリーンアップ実行
            success_list, failed_list = clean_temp_directory(temp_dir)
            
            # 結果をログに記録 (削除があってもなくても実行時間を出力)
            if success_list:
                logging.info(f"{len(success_list)}個のファイル/ディレクトリを削除しました")
            else:
                logging.info("削除対象のファイル/ディレクトリはありませんでした")
                
            if failed_list:
                logging.warning(f"{len(failed_list)}個のファイル/ディレクトリの削除に失敗しました")
            
            # 処理時間を計算
            elapsed_time = time.time() - start_time
            logging.info(f"クリーンアップ完了。処理時間: {elapsed_time:.2f}秒")
            
            # 次の実行までの待機時間を計算（処理時間を考慮）
            wait_time = max(1, cleanup_interval - elapsed_time)
            next_run = datetime.fromtimestamp(time.time() + wait_time)
            logging.info(f"次回のクリーンアップ予定時刻: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"===== クリーンアップ処理終了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
            
            # 指定時間待機
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        logging.info("プログラムが手動で終了されました")
    except Exception as e:
        logging.error(f"予期しないエラーが発生しました: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())