from models import db
from association.models import Estoque, Dispensacao, Membro
from datetime import datetime

class DispensationService:
    @staticmethod
    def dispense_product(associacao_id, membro_id, produto_id, quantidade, prescricao_id=None, observacoes=""):
        """
        Records a dispensation event and updates stock.
        """
        # 1. Validate inputs
        if quantidade <= 0:
            return False, "Quantity must be positive"

        # 2. Check Member status
        membro = Membro.query.get(membro_id)
        if not membro or membro.associacao_id != associacao_id:
            return False, "Member not found in this association"
        if membro.status != 'ativo':
            return False, "Member is not active"

        # 3. Check Stock (FIFO or Specific Batch? For MVP, just total quantity check)
        # In a real scenario, we'd pick specific batches. Here we check if ANY stock exists.
        # Simplification: One consolidated stock entry per product per association? 
        # The model allows multiple batches. We need to deduct from batches.
        
        estoque_items = Estoque.query.filter_by(
            associacao_id=associacao_id, 
            produto_id=produto_id
        ).filter(Estoque.quantidade > 0).order_by(Estoque.validade).all()

        total_available = sum(item.quantidade for item in estoque_items)
        
        if total_available < quantidade:
            return False, f"Insufficient stock. Available: {total_available}"

        # 4. Deduct from Stock (FIFO logic)
        remaining_to_deduct = quantidade
        for item in estoque_items:
            if remaining_to_deduct <= 0:
                break
            
            if item.quantidade >= remaining_to_deduct:
                item.quantidade -= remaining_to_deduct
                remaining_to_deduct = 0
            else:
                remaining_to_deduct -= item.quantidade
                item.quantidade = 0
        
        # 5. Record Dispensation
        dispensacao = Dispensacao(
            associacao_id=associacao_id,
            membro_id=membro_id,
            produto_id=produto_id,
            quantidade=quantidade,
            prescricao_id=prescricao_id,
            observacoes=observacoes,
            data_dispensacao=datetime.utcnow()
        )
        
        db.session.add(dispensacao)
        
        try:
            db.session.commit()
            return True, dispensacao
        except Exception as e:
            db.session.rollback()
            return False, str(e)
