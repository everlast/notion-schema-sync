import os
import json
import requests
import argparse
from dotenv import load_dotenv
from typing import Dict, Any
from colorama import init, Fore, Style

# カラー表示の初期化
init(autoreset=True)

# .envファイルから環境変数を読み込む
load_dotenv()

# Notion API の設定
NOTION_API_TOKEN_PROD = os.getenv("NOTION_API_TOKEN_PROD")
NOTION_API_TOKEN_TEST = os.getenv("NOTION_API_TOKEN_TEST")
PROD_DB_ID = os.getenv("PROD_DB_ID")
TEST_DB_ID = os.getenv("TEST_DB_ID")

# APIヘッダー
def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # 最新のバージョンに更新してください
    }

# データベース情報を取得
def get_database(token, database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    response = requests.get(url, headers=get_headers(token))
    
    if response.status_code != 200:
        print(f"エラー: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

# プロパティをアップデート
def update_database_properties(token, database_id, properties):
    url = f"https://api.notion.com/v1/databases/{database_id}"
    
    data = {
        "properties": properties
    }
    
    response = requests.patch(url, headers=get_headers(token), json=data)
    
    if response.status_code != 200:
        print(f"エラー: {response.status_code}")
        print(response.text)
        return False
    
    return True

# プロパティの差分を検出
def detect_schema_diff(prod_props: Dict[str, Any], test_props: Dict[str, Any]):
    diff = {
        "only_in_prod": {},
        "only_in_test": {},
        "different_config": {}
    }
    
    # 本番環境にのみ存在するプロパティまたは設定が異なるプロパティを検出
    for name, config in prod_props.items():
        if name not in test_props:
            diff["only_in_prod"][name] = config
        elif json.dumps(test_props[name]) != json.dumps(config):
            diff["different_config"][name] = {
                "prod": config,
                "test": test_props[name]
            }
    
    # テスト環境にのみ存在するプロパティを検出
    for name, config in test_props.items():
        if name not in prod_props:
            diff["only_in_test"][name] = config
    
    return diff

# Formula設定の詳細を取得
def get_formula_details(formula_config):
    if not formula_config or "formula" not in formula_config:
        return "不明"
    
    formula = formula_config.get("formula", {})
    
    # 式の種類によって詳細を取得
    if "string" in formula:
        return f"文字列: {formula['string']}"
    elif "number" in formula:
        return f"数値: {formula['number']}"
    elif "boolean" in formula:
        return f"ブール値: {formula['boolean']}"
    elif "date" in formula:
        return f"日付: {formula['date']}"
    elif "expression" in formula:
        return f"式: {json.dumps(formula['expression'], ensure_ascii=False, indent=2)}"
    else:
        return json.dumps(formula, ensure_ascii=False)

# プロパティ設定の詳細を取得
def get_property_details(config):
    prop_type = config.get("type", "不明")
    
    if prop_type == "formula":
        return get_formula_details(config)
    elif prop_type == "select":
        options = config.get("select", {}).get("options", [])
        return f"選択肢: {len(options)}個"
    elif prop_type == "multi_select":
        options = config.get("multi_select", {}).get("options", [])
        return f"選択肢: {len(options)}個"
    elif prop_type == "relation":
        relation = config.get("relation", {})
        return f"関連DB: {relation.get('database_id', '不明')}"
    else:
        return prop_type

# 差分の表示
def print_schema_diff(diff, show_details=True):
    print("\n=== Notion DBスキーマの差分 ===\n")
    
    if not diff["only_in_prod"] and not diff["only_in_test"] and not diff["different_config"]:
        print(Fore.GREEN + "差分はありません。両環境のスキーマは同一です。" + Style.RESET_ALL)
        return
    
    # 本番環境にのみ存在するプロパティ
    if diff["only_in_prod"]:
        print(Fore.RED + "📌 本番環境にのみ存在するプロパティ:" + Style.RESET_ALL)
        for name, config in diff["only_in_prod"].items():
            prop_type = config.get("type", "不明")
            print(Fore.RED + f"  • {name} (タイプ: {prop_type})" + Style.RESET_ALL)
            if show_details and prop_type == "formula":
                details = get_property_details(config)
                print(Fore.RED + f"    → {details}" + Style.RESET_ALL)
        print()
    
    # テスト環境にのみ存在するプロパティ
    if diff["only_in_test"]:
        print(Fore.BLUE + "📌 テスト環境にのみ存在するプロパティ:" + Style.RESET_ALL)
        for name, config in diff["only_in_test"].items():
            prop_type = config.get("type", "不明")
            print(Fore.BLUE + f"  • {name} (タイプ: {prop_type})" + Style.RESET_ALL)
            if show_details and prop_type == "formula":
                details = get_property_details(config)
                print(Fore.BLUE + f"    → {details}" + Style.RESET_ALL)
        print()
    
    # 設定が異なるプロパティ
    if diff["different_config"]:
        print(Fore.YELLOW + "📌 設定が異なるプロパティ:" + Style.RESET_ALL)
        for name, configs in diff["different_config"].items():
            prod_type = configs['prod'].get('type', '不明')
            test_type = configs['test'].get('type', '不明')
            
            print(Fore.YELLOW + f"  • {name}:" + Style.RESET_ALL)
            
            if prod_type != test_type:
                print(f"    - タイプの違い: " + 
                      f"{Fore.WHITE}本番={prod_type}, " + 
                      f"{Fore.YELLOW}テスト={test_type}" + Style.RESET_ALL)
            else:
                print(f"    - タイプ: {prod_type}")
                
                # formulaの場合は詳細を表示（オプションに応じて）
                if show_details and prod_type == "formula":
                    prod_formula = get_formula_details(configs['prod'])
                    test_formula = get_formula_details(configs['test'])
                    
                    print(f"    - 本番の式: {Fore.WHITE}{prod_formula}{Style.RESET_ALL}")
                    print(f"    - テストの式: {Fore.YELLOW}{test_formula}{Style.RESET_ALL}")
                    
                    # formulaの中でexpressionがある場合はさらに詳細な比較
                    if "formula" in configs['prod'] and "expression" in configs['prod']['formula'] and \
                       "formula" in configs['test'] and "expression" in configs['test']['formula']:
                        prod_expr = json.dumps(configs['prod']['formula']['expression'], ensure_ascii=False)
                        test_expr = json.dumps(configs['test']['formula']['expression'], ensure_ascii=False)
                        
                        if prod_expr != test_expr:
                            print(f"    - 式の違い:")
                            prod_expr_formatted = json.dumps(configs['prod']['formula']['expression'], ensure_ascii=False, indent=6)
                            test_expr_formatted = json.dumps(configs['test']['formula']['expression'], ensure_ascii=False, indent=6)
                            
                            # 差分を強調表示
                            highlight_formula_diff(prod_expr_formatted, test_expr_formatted)
                elif show_details:
                    # その他のタイプの場合も主要な差分を表示（オプションに応じて）
                    prod_details = get_property_details(configs['prod'])
                    test_details = get_property_details(configs['test'])
                    
                    if prod_details != test_details:
                        print(f"    - 本番の設定: {Fore.WHITE}{prod_details}{Style.RESET_ALL}")
                        print(f"    - テストの設定: {Fore.YELLOW}{test_details}{Style.RESET_ALL}")
        print()

# フォーミュラの差分を強調表示
def highlight_formula_diff(prod_expr, test_expr):
    prod_lines = prod_expr.split('\n')
    test_lines = test_expr.split('\n')
    
    # 行数の違いを処理
    max_lines = max(len(prod_lines), len(test_lines))
    
    print(f"      {Fore.WHITE}本番:{Style.RESET_ALL}")
    for i in range(len(prod_lines)):
        print(f"      {Fore.WHITE}{prod_lines[i]}{Style.RESET_ALL}")
    
    print(f"      {Fore.YELLOW}テスト:{Style.RESET_ALL}")
    for i in range(len(test_lines)):
        # テスト環境の式が本番と異なる場合は黄色で表示
        if i >= len(prod_lines) or test_lines[i] != prod_lines[i]:
            print(f"      {Fore.YELLOW}{test_lines[i]}{Style.RESET_ALL}")
        else:
            print(f"      {test_lines[i]}")

# メイン処理
def main():
    parser = argparse.ArgumentParser(description="Notion DBスキーマの差分確認・同期ツール")
    parser.add_argument("--diff-only", action="store_true", help="差分の確認のみを行い、同期処理は実行しない")
    parser.add_argument("--sync", action="store_true", help="スキーマの同期を実行する")
    parser.add_argument("--simple", action="store_true", help="フォーミュラや設定の詳細を表示しない簡易表示モード")
    parser.add_argument("--detail", action="store_true", help="フォーミュラや設定の詳細を表示する詳細表示モード（デフォルト）")
    args = parser.parse_args()
    
    # どちらのオプションも指定されていない場合はヘルプを表示
    if not args.diff_only and not args.sync:
        parser.print_help()
        return
    
    # 詳細表示フラグの決定（--simpleが指定されている場合はFalse、それ以外はTrue）
    show_details = not args.simple if args.simple else True
    
    # --detailが明示的に指定されている場合は、--simpleよりも優先
    if args.detail:
        show_details = True
    
    # 本番環境のデータベース情報を取得
    print("本番環境のデータベース情報を取得中...")
    prod_db = get_database(NOTION_API_TOKEN_PROD, PROD_DB_ID)
    if not prod_db:
        print(f"{Fore.RED}本番環境のデータベース情報の取得に失敗しました。{Style.RESET_ALL}")
        return
    
    # テスト環境のデータベース情報を取得
    print("テスト環境のデータベース情報を取得中...")
    test_db = get_database(NOTION_API_TOKEN_TEST, TEST_DB_ID)
    if not test_db:
        print(f"{Fore.RED}テスト環境のデータベース情報の取得に失敗しました。{Style.RESET_ALL}")
        return
    
    # 本番環境とテスト環境のプロパティを取得
    prod_properties = prod_db.get("properties", {})
    test_properties = test_db.get("properties", {})
    
    # 差分を検出
    diff = detect_schema_diff(prod_properties, test_properties)
    
    # 差分を表示（詳細表示オプション付き）
    print_schema_diff(diff, show_details=show_details)
    
    # 表示モードの情報表示
    if show_details:
        print(f"{Fore.CYAN}詳細表示モードで表示しています。簡易表示にするには --simple オプションを使用してください。{Style.RESET_ALL}")
    else:
        print(f"{Fore.CYAN}簡易表示モードで表示しています。詳細表示にするには --detail オプションを使用してください。{Style.RESET_ALL}")
    
    # 同期オプションが指定されている場合のみ同期処理を実行
    if args.sync and not args.diff_only:
        confirm = input(f"\n{Fore.GREEN}本番環境のスキーマをテスト環境に同期しますか？ (y/n): {Style.RESET_ALL}")
        if confirm.lower() == 'y':
            success = update_database_properties(NOTION_API_TOKEN_TEST, TEST_DB_ID, prod_properties)
            
            if success:
                print(f"{Fore.GREEN}データベーススキーマの同期が完了しました！{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}データベーススキーマの同期に失敗しました。{Style.RESET_ALL}")
        else:
            print("同期処理をキャンセルしました。")

if __name__ == "__main__":
    main()
