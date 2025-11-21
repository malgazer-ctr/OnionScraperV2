import json
import os
import glob

# JSONファイルが格納されているディレクトリ
json_dir = r"E:\MonitorSystem\Source\OnionScraperV2\Data\HTMLdiff_Data"

def remove_duplicate_keys(obj):
    """辞書のキーの重複を削除する"""
    if isinstance(obj, dict):
        seen_keys = set()
        new_dict = {}
        changed = False  # 変更があったかを記録
        for key, value in obj.items():
            if key not in seen_keys:
                seen_keys.add(key)
                new_value, was_changed = remove_duplicate_keys(value)
                new_dict[key] = new_value
                if was_changed:
                    changed = True
            else:
                changed = True  # 重複が見つかったので変更ありとする
        return new_dict, changed
    elif isinstance(obj, list):
        new_list = []
        changed = False
        for item in obj:
            new_item, was_changed = remove_duplicate_keys(item)
            new_list.append(new_item)
            if was_changed:
                changed = True
        return new_list, changed
    return obj, False

# 指定フォルダ内の全てのJSONファイルを取得
json_files = glob.glob(os.path.join(json_dir, "*.json"))

# 各JSONファイルに対して処理を実行
for json_file in json_files:
    try:
        # JSONファイルを読み込む
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 重複キーを削除（変更があったかどうかも取得）
        cleaned_data, changed = remove_duplicate_keys(data)

        # 変更があった場合のみ上書き保存
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        print(f"更新: {json_file}")
   

    except Exception as e:
        print(f"エラー: {json_file} の処理中に問題が発生しました - {e}")

print("全ファイルの処理が完了しました。")
