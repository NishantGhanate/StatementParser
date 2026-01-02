"""
NiceGUI Application for Managing Categorization Rules.

Run with:
  cd D:\\Github\\ExpenseBoard\\StatementParser
  python -m app.ui.rules_app

Or with reload:
  nicegui run app/ui/rules_app.py --reload
"""

import os
import re
from dataclasses import dataclass
from typing import Optional

import psycopg
from dotenv import load_dotenv
from nicegui import ui
from psycopg.rows import dict_row

load_dotenv()

# Import rule engine for proper validation
try:
    from app.rule_engine.parser import parse, try_parse
    USE_FULL_PARSER = True
except ImportError:
    USE_FULL_PARSER = False


# =============================================================================
# DSL VALIDATOR
# =============================================================================

class DSLValidator:
    """DSL validator - uses full parser if available, else simple regex."""

    ASSIGNMENTS = {'category_id', 'tag_id', 'type_id', 'payment_method_id', 'goal_id'}

    @classmethod
    def validate(cls, dsl_text: str) -> tuple[bool, str]:
        if not dsl_text or not dsl_text.strip():
            return False, "DSL text is required"

        # Use full parser if available
        if USE_FULL_PARSER:
            result, error = try_parse(dsl_text)
            if error:
                return False, f"❌ {error}"
            return True, "✅ Valid syntax"

        # Fallback to simple validation
        text = dsl_text.strip()
        if not text.lower().startswith('rule'): return False, "Must start with 'rule'"
        if not text.endswith(';'): return False, "Must end with ';'"
        if 'where' not in text.lower(): return False, "Missing 'where'"
        if 'assign' not in text.lower(): return False, "Missing 'assign'"
        if not re.search(r'rule\s+"([^"]+)"', text, re.IGNORECASE): return False, "Rule name must be in quotes"
        if not any(a in text.lower() for a in cls.ASSIGNMENTS): return False, "Missing assignment"
        if text.count('"') % 2 != 0: return False, "Unbalanced quotes"
        return True, "✅ Valid syntax"


# =============================================================================
# DATABASE
# =============================================================================

def get_db_url() -> str:
    return os.getenv("DATABASE_URL")

def get_connection():
    return psycopg.connect(get_db_url(), row_factory=dict_row)


# =============================================================================
# DATA ACCESS
# =============================================================================

@dataclass
class Rule:
    id: Optional[int]
    name: str
    dsl_text: str
    priority: int
    user_id: int
    is_active: bool = True


def fetch_rules(user_id: int = 1) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, dsl_text, priority, user_id, is_active, created_at, updated_at
                FROM ss_categorization_rules WHERE user_id = %s ORDER BY priority ASC, name ASC
            """, (user_id,))
            return cur.fetchall()


def fetch_rule_by_id(rule_id: int) -> Optional[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, dsl_text, priority, user_id, is_active FROM ss_categorization_rules WHERE id = %s", (rule_id,))
            return cur.fetchone()


def save_rule(rule: Rule) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            if rule.id:
                cur.execute("UPDATE ss_categorization_rules SET name = %s, dsl_text = %s, priority = %s, is_active = %s WHERE id = %s RETURNING id",
                           (rule.name, rule.dsl_text, rule.priority, rule.is_active, rule.id))
            else:
                cur.execute("INSERT INTO ss_categorization_rules (name, dsl_text, priority, user_id, is_active) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                           (rule.name, rule.dsl_text, rule.priority, rule.user_id, rule.is_active))
            conn.commit()
            return cur.fetchone()['id']


def delete_rule(rule_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ss_categorization_rules WHERE id = %s", (rule_id,))
            conn.commit()
            return cur.rowcount > 0


def toggle_rule_active(rule_id: int, is_active: bool) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE ss_categorization_rules SET is_active = %s WHERE id = %s", (is_active, rule_id))
            conn.commit()
            return cur.rowcount > 0


def fetch_lookup(query: str) -> list[dict]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
    except:
        return []


def fetch_categories(): return fetch_lookup("SELECT id, name, type, color FROM ss_categories WHERE is_active = TRUE ORDER BY name")
def fetch_tags(): return fetch_lookup("SELECT id, name, color FROM ss_tags WHERE is_active = TRUE ORDER BY name")
def fetch_payment_methods(): return fetch_lookup("SELECT id, type, name, color FROM ss_payment_methods WHERE is_active = TRUE ORDER BY type, name")
def fetch_transaction_types(): return fetch_lookup("SELECT id, name, color FROM ss_transaction_types WHERE is_active = TRUE ORDER BY name")
def fetch_goals(): return fetch_lookup("SELECT id, name, target_amount, status, color FROM ss_goals WHERE status = 'ACTIVE' ORDER BY name")
def fetch_users():
    users = fetch_lookup("SELECT id, name, email FROM ss_users WHERE is_active = TRUE ORDER BY name")
    return users if users else [{'id': 1, 'name': 'Default', 'email': ''}]


# =============================================================================
# DSL HELP
# =============================================================================

DSL_HELP = """
## Rule Syntax
```
rule "Rule Name" where <conditions> assign <assignments> priority <number>;
```

## Transaction Fields
| Field | Description |
|-------|-------------|
| `description` | Transaction narration |
| `entity_name` | Payee/receiver name |
| `amount` | Transaction amount |
| `type` | "credit" or "debit" |

## Operators
| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `type:eq:"credit"` |
| `neq` | Not equals | `type:neq:"credit"` |
| `gt` | Greater than | `amount:gt:"50000"` |
| `lt` | Less than | `amount:lt:"1000"` |
| `gte` | Greater or equal | `amount:gte:"10000"` |
| `lte` | Less or equal | `amount:lte:"5000"` |
| `between` | Range (inclusive) | `amount:between:"1000":"5000"` |
| `con` | Contains (any) | `description:con:"UPI","NEFT"` |
| `noc` | Not contains | `description:noc:"SPAM"` |
| `sw` | Starts with | `description:sw:"UPI/"` |
| `ew` | Ends with | `entity_name:ew:"BANK"` |
| `regex` | Regex match | `description:regex:"SALARY\\|PAYROLL"` |
| `in` | In list | `type:in:"credit","debit"` |
| `nin` | Not in list | `entity_name:nin:"SELF","OWN"` |
| `null` | Is empty | `remarks:null` |
| `nnull` | Not empty | `entity_name:nnull` |

## Case Insensitive
Add `:i` at the end for case-insensitive:
```
description:sw:"UPI":i
entity_name:con:"KANTI":i
```

## Combine Conditions
**AND**: `description:sw:"UPI":i and type:eq:"debit"`
**OR**: `description:sw:"UPI":i or description:sw:"IMPS":i`

## Assignments
| Field | Description |
|-------|-------------|
| `category_id` | Category ID |
| `tag_id` | Tag ID |
| `type_id` | Transaction type (1=Credit, 2=Debit, 3=Transfer) |
| `payment_method_id` | Payment method ID |
| `goal_id` | Financial goal ID |

## Examples
```
rule "UPI Payment" where description:sw:"UPI":i assign payment_method_id:1 priority 100;

rule "Salary" where description:regex:"SALARY|PAYROLL":i and type:eq:"credit":i
    assign category_id:1 type_id:1 priority 10;

rule "SIP" where entity_name:sw:"Indian Cle":i and type:eq:"debit"
    assign category_id:2 type_id:2 goal_id:1 tag_id:1 priority 15;

rule "Large Txn" where amount:gt:"50000" assign tag_id:2 priority 100;
```
"""


# =============================================================================
# UI APPLICATION
# =============================================================================

class RulesApp:
    def __init__(self):
        self.current_user_id = 1
        self.rules = []
        self.categories = []
        self.tags = []
        self.payment_methods = []
        self.transaction_types = []
        self.goals = []
        self.users = []
        self.editing_rule_id = None

        # UI references
        self.rules_container = None
        self.name_input = None
        self.dsl_input = None
        self.priority_input = None
        self.active_switch = None
        self.validation_label = None
        self.form_title = None
        self.save_button = None

    def load_data(self):
        try:
            self.rules = fetch_rules(self.current_user_id)
            self.categories = fetch_categories()
            self.tags = fetch_tags()
            self.payment_methods = fetch_payment_methods()
            self.transaction_types = fetch_transaction_types()
            self.goals = fetch_goals()
            self.users = fetch_users()
        except Exception as e:
            ui.notify(f"Error loading data: {e}", type="negative")

    def on_dsl_change(self, e):
        is_valid, msg = DSLValidator.validate(e.value)
        if self.validation_label:
            self.validation_label.text = msg
            self.validation_label.classes(remove='text-green-600 text-red-600')
            self.validation_label.classes(add='text-green-600' if is_valid else 'text-red-600')

    def reset_form(self):
        self.editing_rule_id = None
        if self.name_input: self.name_input.value = ""
        if self.dsl_input: self.dsl_input.value = ""
        if self.priority_input: self.priority_input.value = 100
        if self.active_switch: self.active_switch.value = True
        if self.validation_label: self.validation_label.text = ""
        if self.form_title: self.form_title.text = "Create New Rule"
        if self.save_button: self.save_button.text = "Create Rule"

    def edit_rule(self, rule_id: int):
        rule = fetch_rule_by_id(rule_id)
        if rule:
            self.editing_rule_id = rule_id
            if self.name_input: self.name_input.value = rule['name']
            if self.dsl_input: self.dsl_input.value = rule['dsl_text']
            if self.priority_input: self.priority_input.value = rule['priority']
            if self.active_switch: self.active_switch.value = rule['is_active']
            if self.form_title: self.form_title.text = f"Edit: {rule['name']}"
            if self.save_button: self.save_button.text = "Update Rule"
            is_valid, msg = DSLValidator.validate(rule['dsl_text'])
            if self.validation_label: self.validation_label.text = msg

    async def save_rule_handler(self):
        name = self.name_input.value.strip() if self.name_input else ""
        dsl_text = self.dsl_input.value.strip() if self.dsl_input else ""
        priority = int(self.priority_input.value) if self.priority_input else 100
        is_active = self.active_switch.value if self.active_switch else True

        if not name:
            ui.notify("Rule name is required", type="warning")
            return

        is_valid, error = DSLValidator.validate(dsl_text)
        if not is_valid:
            ui.notify(f"Invalid DSL: {error}", type="negative")
            return

        try:
            rule = Rule(id=self.editing_rule_id, name=name, dsl_text=dsl_text, priority=priority, user_id=self.current_user_id, is_active=is_active)
            save_rule(rule)
            action = "updated" if self.editing_rule_id else "created"
            ui.notify(f"Rule '{name}' {action}!", type="positive")
            self.reset_form()
            self.load_data()
            self.refresh_rules_list()
        except Exception as e:
            ui.notify(f"Error: {e}", type="negative")

    async def delete_rule_handler(self, rule_id: int, rule_name: str):
        with ui.dialog() as dialog, ui.card():
            ui.label(f"Delete '{rule_name}'?").classes('text-lg font-bold')
            ui.label("This cannot be undone.").classes('text-gray-600')
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                async def confirm():
                    delete_rule(rule_id)
                    ui.notify(f"Deleted '{rule_name}'", type="positive")
                    dialog.close()
                    self.load_data()
                    self.refresh_rules_list()
                    if self.editing_rule_id == rule_id: self.reset_form()
                ui.button('Delete', on_click=confirm).props('color=negative')
        dialog.open()

    def refresh_rules_list(self):
        if self.rules_container:
            self.rules_container.clear()
            with self.rules_container:
                self.render_rules_list()

    def get_name(self, lookup: list[dict], id_val: Optional[int], key: str = 'name') -> str:
        if id_val is None: return "-"
        for item in lookup:
            if item['id'] == id_val: return item[key]
        return f"ID:{id_val}"

    def parse_assignments(self, dsl: str) -> dict:
        """Extract assignments from DSL using full parser or regex fallback."""
        if USE_FULL_PARSER:
            try:
                rule = parse(dsl)
                return {
                    'category_id': rule.assignment.category_id,
                    'tag_id': rule.assignment.tag_id,
                    'type_id': rule.assignment.type_id,
                    'payment_method_id': rule.assignment.payment_method_id,
                    'goal_id': rule.assignment.goal_id,
                }
            except:
                pass

        # Fallback to regex
        result = {}
        for field in ['category_id', 'tag_id', 'type_id', 'payment_method_id', 'goal_id']:
            match = re.search(rf'{field}:(\d+)', dsl, re.IGNORECASE)
            if match: result[field] = int(match.group(1))
        return result

    def render_rules_list(self):
        if not self.rules:
            ui.label("No rules found. Create your first rule!").classes('text-gray-500 italic p-4')
            return

        for rule in self.rules:
            assigns = self.parse_assignments(rule['dsl_text'])
            with ui.card().classes('w-full mb-2 p-3' + (' opacity-60' if not rule['is_active'] else '')):
                with ui.row().classes('w-full items-center'):
                    ui.badge(str(rule['priority']), color='blue').classes('mr-2').tooltip('Priority')

                    with ui.column().classes('flex-1'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(rule['name']).classes('font-bold text-lg')
                            if not rule['is_active']:
                                ui.badge('Inactive', color='grey')

                        with ui.row().classes('gap-1 flex-wrap mt-1'):
                            if assigns.get('category_id'):
                                ui.chip(f"📁 {self.get_name(self.categories, assigns.get('category_id'))}", color='green').props('dense outline')
                            if assigns.get('tag_id'):
                                ui.chip(f"🏷️ {self.get_name(self.tags, assigns.get('tag_id'))}", color='orange').props('dense outline')
                            if assigns.get('type_id'):
                                ui.chip(f"📊 {self.get_name(self.transaction_types, assigns.get('type_id'))}", color='purple').props('dense outline')
                            if assigns.get('payment_method_id'):
                                ui.chip(f"💳 {self.get_name(self.payment_methods, assigns.get('payment_method_id'))}", color='blue').props('dense outline')
                            if assigns.get('goal_id'):
                                ui.chip(f"🎯 {self.get_name(self.goals, assigns.get('goal_id'))}", color='teal').props('dense outline')

                    with ui.row().classes('gap-1'):
                        ui.button(icon='edit', on_click=lambda r=rule: self.edit_rule(r['id'])).props('flat dense color=primary').tooltip('Edit')
                        ui.button(icon='content_copy', on_click=lambda r=rule: self.duplicate_rule(r)).props('flat dense color=secondary').tooltip('Duplicate')
                        ui.button(icon='visibility', on_click=lambda r=rule: self.show_dsl(r['name'], r['dsl_text'])).props('flat dense color=grey').tooltip('View DSL')
                        ui.button(icon='delete', on_click=lambda r=rule: self.delete_rule_handler(r['id'], r['name'])).props('flat dense color=negative').tooltip('Delete')
                        ui.switch('', value=rule['is_active'], on_change=lambda e, r=rule: self.toggle_active(r['id'], e.value)).tooltip('Active')

    def toggle_active(self, rule_id: int, is_active: bool):
        toggle_rule_active(rule_id, is_active)
        ui.notify(f"Rule {'activated' if is_active else 'deactivated'}")
        self.load_data()
        self.refresh_rules_list()

    def duplicate_rule(self, rule: dict):
        """Duplicate a rule into the form."""
        if self.name_input: self.name_input.value = f"{rule['name']} (copy)"
        if self.dsl_input:
            # Update the name in DSL too
            dsl = re.sub(r'rule\s+"[^"]+"', f'rule "{rule["name"]} (copy)"', rule['dsl_text'], flags=re.IGNORECASE)
            self.dsl_input.value = dsl
        if self.priority_input: self.priority_input.value = rule['priority']
        if self.active_switch: self.active_switch.value = True
        if self.form_title: self.form_title.text = "Create New Rule (from copy)"
        if self.save_button: self.save_button.text = "Create Rule"
        self.editing_rule_id = None  # Create new, not edit
        is_valid, msg = DSLValidator.validate(self.dsl_input.value if self.dsl_input else "")
        if self.validation_label: self.validation_label.text = msg

    def show_dsl(self, name: str, dsl: str):
        with ui.dialog() as d, ui.card().classes('w-[700px]'):
            ui.label(f"Rule: {name}").classes('text-lg font-bold')
            ui.code(dsl, language='sql').classes('w-full')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Copy', on_click=lambda: (ui.clipboard.write(dsl), ui.notify('Copied!'))).props('flat')
                ui.button('Close', on_click=d.close).props('flat')
        d.open()

    def render_lookups(self):
        with ui.expansion('📋 Reference Tables (IDs)', icon='table_chart').classes('w-full'):
            with ui.tabs().classes('w-full') as tabs:
                t1, t2, t3, t4, t5 = ui.tab('Categories'), ui.tab('Tags'), ui.tab('Types'), ui.tab('Payments'), ui.tab('Goals')

            with ui.tab_panels(tabs, value=t1).classes('w-full'):
                with ui.tab_panel(t1):
                    if self.categories:
                        with ui.row().classes('gap-2 flex-wrap'):
                            for c in self.categories:
                                ui.chip(f"{c['id']}: {c['name']} ({c.get('type','')})", color=c.get('color','grey')).props('dense')
                    else:
                        ui.label("No categories found").classes('text-gray-500 italic')

                with ui.tab_panel(t2):
                    if self.tags:
                        with ui.row().classes('gap-2 flex-wrap'):
                            for t in self.tags:
                                ui.chip(f"{t['id']}: {t['name']}", color=t.get('color','grey')).props('dense')
                    else:
                        ui.label("No tags found").classes('text-gray-500 italic')

                with ui.tab_panel(t3):
                    if self.transaction_types:
                        with ui.row().classes('gap-2 flex-wrap'):
                            for t in self.transaction_types:
                                ui.chip(f"{t['id']}: {t['name']}", color=t.get('color','grey')).props('dense')
                    else:
                        ui.label("No types found").classes('text-gray-500 italic')

                with ui.tab_panel(t4):
                    if self.payment_methods:
                        with ui.row().classes('gap-2 flex-wrap'):
                            for p in self.payment_methods:
                                ui.chip(f"{p['id']}: {p['type']}-{p['name']}", color=p.get('color','grey')).props('dense')
                    else:
                        ui.label("No payment methods found").classes('text-gray-500 italic')

                with ui.tab_panel(t5):
                    if self.goals:
                        with ui.row().classes('gap-2 flex-wrap'):
                            for g in self.goals:
                                ui.chip(f"{g['id']}: {g['name']}", color=g.get('color','grey')).props('dense')
                    else:
                        ui.label("No active goals found").classes('text-gray-500 italic')

    def apply_template(self, name: str, dsl: str):
        if self.name_input: self.name_input.value = name
        if self.dsl_input: self.dsl_input.value = dsl
        if self.form_title: self.form_title.text = "Create New Rule"
        if self.save_button: self.save_button.text = "Create Rule"
        self.editing_rule_id = None
        is_valid, msg = DSLValidator.validate(dsl)
        if self.validation_label:
            self.validation_label.text = msg
            self.validation_label.classes(remove='text-green-600 text-red-600')
            self.validation_label.classes(add='text-green-600' if is_valid else 'text-red-600')

    def change_user(self, user_id: int):
        self.current_user_id = user_id
        self.load_data()
        self.refresh_rules_list()
        self.reset_form()
        ui.notify(f"Switched to user {user_id}")

    def build_ui(self):
        self.load_data()
        ui.dark_mode().enable()

        # Header
        with ui.header().classes('bg-blue-800 text-white items-center'):
            ui.label('🏦 ExpenseBoard Rules Manager').classes('text-xl font-bold')
            ui.space()
            ui.label(f"Parser: {'Full' if USE_FULL_PARSER else 'Simple'}").classes('text-sm opacity-75')
            with ui.row().classes('gap-4 items-center'):
                ui.select(
                    label='User',
                    options={u['id']: u['name'] for u in self.users},
                    value=self.current_user_id,
                    on_change=lambda e: self.change_user(e.value)
                ).props('dark dense').classes('w-40')
                ui.button(icon='refresh', on_click=lambda: (self.load_data(), self.refresh_rules_list(), ui.notify("Refreshed"))).props('flat color=white')

        # Main content
        with ui.row().classes('w-full gap-4 p-4'):
            # Left panel - Form
            with ui.card().classes('w-[450px]'):
                self.form_title = ui.label("Create New Rule").classes('text-xl font-bold mb-4')

                self.name_input = ui.input(
                    label='Rule Name',
                    placeholder='e.g., UPI Payment'
                ).classes('w-full')

                self.priority_input = ui.number(
                    label='Priority (lower = higher priority)',
                    value=100, min=1, max=1000, step=10
                ).classes('w-full')

                self.dsl_input = ui.textarea(
                    label='DSL Rule',
                    placeholder='rule "Name" where ... assign ... priority N;'
                ).classes('w-full h-48 font-mono text-sm').on('change', self.on_dsl_change)

                self.validation_label = ui.label().classes('text-sm mt-1')

                with ui.row().classes('w-full items-center gap-4 mt-2'):
                    self.active_switch = ui.switch('Active', value=True)
                    ui.space()
                    ui.button('Clear', on_click=self.reset_form).props('flat')
                    self.save_button = ui.button('Create Rule', on_click=self.save_rule_handler).props('color=primary')

                ui.separator().classes('my-4')

                # Templates
                with ui.expansion('⚡ Quick Templates', icon='flash_on').classes('w-full'):
                    templates = [
                        ("UPI Payment", 'rule "UPI Payment" where description:sw:"UPI":i assign payment_method_id:1 priority 100;'),
                        ("NEFT Payment", 'rule "NEFT Payment" where description:sw:"NEFT":i assign payment_method_id:10 priority 100;'),
                        ("IMPS Payment", 'rule "IMPS Payment" where description:sw:"IMPS":i assign payment_method_id:3 priority 100;'),
                        ("Salary Credit", 'rule "Salary Credit" where description:regex:"SALARY|PAYROLL":i and type:eq:"credit":i assign category_id:1 type_id:1 priority 10;'),
                        ("Investment SIP", 'rule "Investment SIP" where description:regex:"MF|SIP|GROWW|ZERODHA":i and type:eq:"debit":i assign category_id:3 type_id:2 priority 20;'),
                        ("Large Transaction", 'rule "Large Transaction" where amount:gt:"50000" assign tag_id:2 priority 100;'),
                        ("ATM Withdrawal", 'rule "ATM Withdrawal" where description:con:"ATM","CASH":i assign category_id:6 payment_method_id:4 priority 30;'),
                        ("Credit Fallback", 'rule "Credit Fallback" where type:eq:"credit":i assign type_id:1 priority 200;'),
                        ("Debit Fallback", 'rule "Debit Fallback" where type:eq:"debit":i assign type_id:2 priority 200;'),
                    ]
                    for name, tpl in templates:
                        ui.button(name, on_click=lambda t=tpl, n=name: self.apply_template(n, t)).props('flat dense').classes('text-left w-full justify-start')

            # Right panel - Rules list
            with ui.card().classes('flex-1'):
                with ui.row().classes('w-full items-center mb-4'):
                    ui.label("📋 Existing Rules").classes('text-xl font-bold')
                    ui.space()
                    ui.badge(f"{len(self.rules)} rules", color='blue')

                with ui.scroll_area().classes('w-full h-[500px]'):
                    self.rules_container = ui.column().classes('w-full')
                    with self.rules_container:
                        self.render_rules_list()

        # Bottom panels
        with ui.row().classes('w-full gap-4 px-4 pb-4'):
            with ui.card().classes('flex-1'):
                self.render_lookups()

            with ui.card().classes('flex-1'):
                with ui.expansion('📖 DSL Syntax Help', icon='help_outline').classes('w-full'):
                    ui.markdown(DSL_HELP).classes('prose max-w-none prose-sm')


# =============================================================================
# MAIN
# =============================================================================

def main():
    app = RulesApp()
    app.build_ui()
    ui.run(
        title='ExpenseBoard Rules Manager',
        port=8085,
        reload=False,
        show=True
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
