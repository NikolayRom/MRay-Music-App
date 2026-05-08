"""Add gin index for artist name

Revision ID: 83e65cb6b83d
Revises: 1fe53648ef19
Create Date: 2026-05-08 07:42:56.008985

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "83e65cb6b83d"
down_revision: Union[str, Sequence[str], None] = "1fe53648ef19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    op.create_index(
        'idx_artist_name_trgm',
        'artists',
        ['name'],
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'}
    )

def downgrade():
    op.drop_index('idx_artist_name_trgm', table_name='artists')