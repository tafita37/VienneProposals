"""Logique partagée par la création, la modification, l'aperçu, le détail et le PDF des propositions.

La proposition en cours de saisie est stockée en session. La création et la modification
manipulent exactement les mêmes données : seules les clés de session changent
(suffixe « _edit » pour la modification), d'où la classe ProposalSession.

Une « ligne » est la forme normalisée d'un produit de proposition, qu'il vienne de la
session ou de la base : c'est ce que consomment les calculs de totaux et les templates.
"""
import ast
from datetime import date, timedelta

TVA_RATE = 0.2
DEFAULT_VALIDITY_DAYS = 30
UNCATEGORIZED = 'Non catégorisé'

DEFAULT_NO_INCLUDED = """- Alarmes, et Vidéo Surveillance
- Prestations Informatiques et téléphoniques (sauf câblage)
- Démarches auprès des concessionnaires (eau, électricité, téléphonie) (Les arrivées électricité, télécom et eau sont supposées être en attente dans la cellule.)
- Spécificités Incendie particulières (extincteurs, alarme incendie...)
- Honoraires d'un éventuel bureau de contrôle, et du SPS
- Toute prestation : de gros œuvre de pérennité dans les murs, toiture et dalle béton. sur le mobilier et agencement (Devis ArchiBô) en extérieur (toiture, façade, enseignes etc.) sur les Menuiseries extérieures"""

DEFAULT_CGV = """- 40% d'acompte à la signature
- 40% d'acompte à la situation travaux
- 20% d'acompte à la levée des réserves"""


# ────────── Conversions ──────────

def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_positive_float(value):
    return max(0.0, to_float(value))


def to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_iso_date(value, default=None):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return default


def tva_amount(amount_ht, include_tva):
    return amount_ht * TVA_RATE if include_tva else 0.0


# ────────── Textes multilignes (« Non compris », « Conditions de règlement ») ──────────
# Format de stockage historique (session et base) : les retours à la ligne sont
# enregistrés sous la forme littérale « \n ». Les anciennes valeurs, produites par
# repr(), peuvent en plus être entourées d'apostrophes parasites ou contenir « \' ».

def encode_multiline(value):
    """Texte saisi -> format de stockage."""
    if not isinstance(value, str):
        return ''
    return value.replace('\r\n', '\n').replace('\n', '\\n')


def decode_multiline(stored):
    """Format de stockage -> texte affichable dans un textarea."""
    if not stored:
        return ''

    text = str(stored)
    if len(text) >= 2 and text[0] == text[-1] == "'":
        text = text[1:-1]

    try:
        decoded = ast.literal_eval('"' + text + '"')
        if isinstance(decoded, str):
            return decoded
    except (SyntaxError, ValueError):
        pass
    return text.replace('\\n', '\n')


def multiline_items(stored):
    """Format de stockage -> liste des lignes non vides, sans le tiret de début de ligne."""
    items = []
    for line in decode_multiline(stored).split('\n'):
        line = line.strip()
        if line.startswith('- '):
            line = line[2:].strip()
        if line:
            items.append(line)
    return items


# ────────── Produits et lignes de proposition ──────────

def product_category_label(product):
    if product is None:
        return UNCATEGORIZED

    category_names = getattr(product, 'category_names', '')
    if category_names:
        return category_names

    category = getattr(product, 'category', None)
    if category is not None and getattr(category, 'name', ''):
        return category.name

    return UNCATEGORIZED


def make_session_item(product_id, designation, unit, category_name, sale_unit_price, purchase_unit_price,
                      coefficient, quantity, explanation='', price_overridden=False):
    """Construit une ligne au format stocké en session (et renvoyé au JS)."""
    sale_unit_price = max(0.0, sale_unit_price)
    purchase_unit_price = max(0.0, purchase_unit_price)
    coefficient = max(0.0, coefficient)
    quantity = max(0.0, quantity)

    return {
        'product': {
            'id': product_id,
            'designation': designation,
            'unit': unit,
            'category_name': category_name,
            'sale_unit_price': sale_unit_price,
            'purchase_unit_price': purchase_unit_price,
            'prix_unitaire_vente': sale_unit_price * coefficient,
            'prix_unitaire_achat': purchase_unit_price,
            'total': sale_unit_price * coefficient * quantity,
        },
        'coefficient': coefficient,
        'quantity': quantity,
        'explanation': explanation,
        'price_overridden': price_overridden,
    }


def session_line(item):
    """Normalise une ligne stockée en session. Renvoie None si elle est inexploitable."""
    if not isinstance(item, dict):
        return None

    product = item.get('product')
    if not isinstance(product, dict):
        product = {}

    quantity = to_positive_float(item.get('quantity', 0))
    coefficient = to_positive_float(item.get('coefficient', 0))
    sale_unit_price = to_positive_float(product.get('sale_unit_price', product.get('prix_unitaire_vente', 0)))
    purchase_unit_price = to_positive_float(product.get('purchase_unit_price', product.get('prix_unitaire_achat', 0)))
    stored_total = to_positive_float(product.get('total', 0))

    # Ancien format sans prix unitaire : on le déduit du total
    if sale_unit_price <= 0 and coefficient > 0 and quantity > 0:
        sale_unit_price = stored_total / (coefficient * quantity)

    return {
        'product_id': to_int(product.get('id', 0)),
        'designation': str(product.get('designation', '') or '').strip(),
        'unit': str(product.get('unit', '') or '').strip(),
        'category_name': str(product.get('category_name', '') or '').strip() or UNCATEGORIZED,
        'quantity': quantity,
        'coefficient': coefficient,
        'sale_unit_price': sale_unit_price,
        'purchase_unit_price': purchase_unit_price,
        'total': stored_total or sale_unit_price * coefficient * quantity,
        'explanation': str(item.get('explanation', '') or '').strip(),
        'price_overridden': bool(item.get('price_overridden', False)),
    }


def session_lines(items):
    if not isinstance(items, list):
        return []
    return [line for line in map(session_line, items) if line is not None]


def billable_lines(items):
    """Lignes de session à enregistrer en base : celles dont la quantité est positive."""
    return [line for line in session_lines(items) if line['quantity'] > 0]


def session_item_from_line(line):
    return make_session_item(
        product_id=line['product_id'],
        designation=line['designation'],
        unit=line['unit'],
        category_name=line['category_name'],
        sale_unit_price=line['sale_unit_price'],
        purchase_unit_price=line['purchase_unit_price'],
        coefficient=line['coefficient'],
        quantity=line['quantity'],
        explanation=line['explanation'],
        price_overridden=line['price_overridden'],
    )


def proposal_product_line(proposal_product):
    """Normalise un ProposalProduct enregistré en base."""
    product = proposal_product.product
    quantity = to_positive_float(proposal_product.quantity)
    coefficient = to_positive_float(proposal_product.coefficient)
    sale_unit_price = to_positive_float(proposal_product.sale_unit_price)

    designation = str(product.designation or '').strip() if product is not None else ''

    return {
        'product_id': product.id if product is not None else 0,
        'designation': designation or f'Produit {proposal_product.id}',
        'unit': product.unit.name if product is not None and product.unit is not None else '',
        'category_name': product_category_label(product),
        'quantity': quantity,
        'coefficient': coefficient,
        'sale_unit_price': sale_unit_price,
        'purchase_unit_price': to_positive_float(proposal_product.purchase_unit_price),
        'total': quantity * coefficient * sale_unit_price,
        'explanation': str(proposal_product.explanation or '').strip(),
        'price_overridden': False,
    }


def proposal_lines(commercial_proposal):
    proposal_products = (
        commercial_proposal.proposal_products
        .select_related('product__unit')
        .prefetch_related('product__categories')
        .order_by('id')
    )
    return [proposal_product_line(proposal_product) for proposal_product in proposal_products]


def lines_total(lines):
    return sum(line['total'] for line in lines)


def build_summary(lines):
    """Regroupe les lignes par catégorie. Renvoie (catégories, total HT)."""
    categories = {}
    for line in lines:
        category = categories.setdefault(line['category_name'], {
            'name': line['category_name'],
            'items': [],
            'total': 0.0,
        })
        category['items'].append(line)
        category['total'] += line['total']

    return list(categories.values()), lines_total(lines)


# ────────── Proposition en cours de saisie (session) ──────────

class ProposalSession:
    """Accès à la proposition en cours de création (edit=False) ou de modification (edit=True)."""

    FIELDS = (
        'items',
        'client_id',
        'date_proposition',
        'expiration_date',
        'include_tva',
        'project_name',
        'installation_address',
        'no_included',
        'cgv',
        'commercial_proposal_number',
    )
    # Brouillon en cours de modification : clé commune, historiquement sans suffixe
    DRAFT_ID_KEY = 'proposal_draft_id'

    def __init__(self, request, edit=False):
        self.session = request.session
        self.edit = edit
        self.preview_url_name = 'appercu_proposition_page_edit' if edit else 'appercu_proposition_page'

    def key(self, field):
        base = 'proposal' if field == 'items' else f'proposal_{field}'
        return f'{base}_edit' if self.edit else base

    def get(self, field, default=None):
        return self.session.get(self.key(field), default)

    def set(self, field, value):
        self.session[self.key(field)] = value
        self.session.modified = True

    @property
    def items(self):
        items = self.get('items', [])
        return items if isinstance(items, list) else []

    @items.setter
    def items(self, value):
        self.set('items', value)

    @property
    def lines(self):
        return session_lines(self.items)

    @property
    def client_id(self):
        return to_int(self.get('client_id'), default=None)

    @property
    def proposal_date(self):
        return parse_iso_date(self.get('date_proposition'), default=date.today())

    @property
    def expiration_date(self):
        default = self.proposal_date + timedelta(days=DEFAULT_VALIDITY_DAYS)
        return parse_iso_date(self.get('expiration_date'), default=default)

    @property
    def include_tva(self):
        return bool(self.get('include_tva', True))

    @property
    def draft_id(self):
        return to_int(self.session.get(self.DRAFT_ID_KEY), default=None) if self.edit else None

    def clear(self):
        keys = [self.key(field) for field in self.FIELDS]
        if self.edit:
            keys.append(self.DRAFT_ID_KEY)
        for key in keys:
            self.session.pop(key, None)
        self.session.modified = True

    def load_from_proposal(self, commercial_proposal):
        """Charge un brouillon enregistré en base dans la session de modification."""
        self.items = [session_item_from_line(line) for line in proposal_lines(commercial_proposal)]
        self.set('client_id', commercial_proposal.client_id)
        self.set('date_proposition', commercial_proposal.date_proposal.isoformat() if commercial_proposal.date_proposal else '')

        expiration_date = commercial_proposal.expiration_date
        if expiration_date is None and commercial_proposal.date_proposal:
            expiration_date = commercial_proposal.date_proposal + timedelta(days=DEFAULT_VALIDITY_DAYS)
        self.set('expiration_date', expiration_date.isoformat() if expiration_date else '')

        self.set('include_tva', float(commercial_proposal.amount_ttc or 0) > float(commercial_proposal.amount_ht or 0))
        self.set('project_name', commercial_proposal.project_name or '')
        self.set('installation_address', commercial_proposal.installation_address or '')
        self.set('no_included', commercial_proposal.no_included or '')
        self.set('cgv', commercial_proposal.cgv or '')
        self.set('commercial_proposal_number', commercial_proposal.commercial_proposal_number or '')
        self.session[self.DRAFT_ID_KEY] = commercial_proposal.id
