import os
import json
import csv
from datetime import datetime
import glob

def process_victim_lists(directory, output_file, output_file_json, start_year_month=None, end_year_month=None):
    json_files = glob.glob(os.path.join(directory, '*_VictimsListAll.json'))
    
    output_data = []
    output_data_json = []
    try:
        for json_file in json_files:
            filename = os.path.basename(json_file)
            attack_group = filename.rsplit('_VictimsListAll.json', 1)[0]
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for key, value in data.items():
                detectedDate = value.get('detectedDate', '')
                if detectedDate:
                    detected_date = datetime.strptime(detectedDate, "%Y/%m/%d %H:%M")
                    detected_year_month = detected_date.strftime("%Y/%m")
                    
                    # 年月のみでフィルタリング
                    if start_year_month and end_year_month:
                        if not (start_year_month <= detected_year_month <= end_year_month):
                            continue
                    elif start_year_month:
                        if detected_year_month < start_year_month:
                            continue
                    elif end_year_month:
                        if detected_year_month > end_year_month:
                            continue

                    aiInvestigatement = value.get('aiInvestigatement', {})
                    if aiInvestigatement:
                        debug = 1
                    
                    row = [
                        "Leak Site",
                        "",
                        "",
                        attack_group,
                        value['detectedDate'],
                        value.get('updateDate', ''),
                        "",
                        key,
                        value.get('summary', ''),
                        value.get('summary_JP', ''),
                        value.get('searchOnGenerativeAI', '')
                    ]
                    output_data.append(row)

                    newDicData = {}
                    newDicData[key] = data[key]
                    newDicData[key]['groupName'] = attack_group
                    output_data_json.append(newDicData)
        
        # CSVに書き込み
        with open(output_file, 'w', newline='', encoding='utf_8_sig') as f:
            writer = csv.writer(f)
            writer.writerows(output_data)

        # 新しいJSONファイルに書き込み
        with open(output_file_json, 'w', encoding='utf_8_sig') as f:
            json.dump(output_data_json, f, ensure_ascii=False, indent=4)
    
    except Exception as e:
        print(str(e))

# 使用例:
targetStartYear = 2025
targetStartMonth = 10
targetEndYear = 2025
targetEndMonth = 11
process_victim_lists(r'E:\MonitorSystem\Source\OnionScraperV2\Data\HTMLdiff_Data',
                     fr'E:\MonitorSystem\Source\OnionScraperV2\Data\リークサイト掲載データ_{targetStartYear}{targetStartMonth:02d}-{targetEndYear}{targetEndMonth:02d}.csv',
                     fr'E:\MonitorSystem\Source\OnionScraperV2\Data\リークサイト掲載データ_{targetStartYear}{targetStartMonth:02d}-{targetEndYear}{targetEndMonth:02d}.json',
                     start_year_month=f'{targetStartYear}/{targetStartMonth:02d}',
                     end_year_month=f'{targetEndYear}/{targetEndMonth:02d}')