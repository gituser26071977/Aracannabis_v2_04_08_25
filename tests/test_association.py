import unittest
from app_cors_livre import create_app
from models import db, Produto
from association.models import Estoque

class TestAssociation(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create Dummy Product
            self.prod = Produto(nome="Cannabis Oil", tipo="oleo", concentracao_cbd=5)
            db.session.add(self.prod)
            db.session.commit()
            self.prod_id = self.prod.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_association(self):
        resp = self.client.post('/api/association/associations', json={
            'nome': 'Assoc Test',
            'cnpj': '12345678000199',
            'email': 'contato@assoc.com'
        })
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json['id'] > 0)

    def test_create_member_and_stock_flow(self):
        # 1. Create Assoc
        resp = self.client.post('/api/association/associations', json={
            'nome': 'Assoc Flow', 'cnpj': '999', 'email': 'flow@assoc.com'
        })
        assoc_id = resp.json['id']

        # 2. Add Member
        resp = self.client.post(f'/api/association/associations/{assoc_id}/members', json={
            'nome': 'John Doe', 'cpf': '11122233344'
        })
        self.assertEqual(resp.status_code, 201)
        member_id = resp.json['member']['id']

        # 3. Add Stock
        resp = self.client.post(f'/api/association/associations/{assoc_id}/stock', json={
            'produto_id': self.prod_id,
            'quantidade': 10,
            'lote': 'BATCH01',
            'validade': '2030-01-01'
        })
        self.assertEqual(resp.status_code, 201)

        # 4. Dispense Successful
        resp = self.client.post(f'/api/association/associations/{assoc_id}/dispense', json={
            'membro_id': member_id,
            'produto_id': self.prod_id,
            'quantidade': 3
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['quantidade'], 3)

        # 5. Verify Stock Reduced
        with self.app.app_context():
            stock = Estoque.query.filter_by(associacao_id=assoc_id).first()
            self.assertEqual(stock.quantidade, 7)

        # 6. Dispense Fail (Insufficient)
        resp = self.client.post(f'/api/association/associations/{assoc_id}/dispense', json={
            'membro_id': member_id,
            'produto_id': self.prod_id,
            'quantidade': 999
        })
        self.assertEqual(resp.status_code, 400)

if __name__ == '__main__':
    unittest.main()
