"""Add GIN index for album name

Revision ID: 525c926680b3
Revises: 83e65cb6b83d
Create Date: 2026-05-08 16:19:40.706520

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "525c926680b3"
down_revision: Union[str, Sequence[str], None] = "83e65cb6b83d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    op.create_index(
        'idx_album_name_trgm',
        'albums',
        ['name'],
        postgresql_using='gin',
        postgresql_ops={'name': 'gin_trgm_ops'}
    )

def downgrade():
    op.drop_index('idx_album_name_trgm', table_name='albums')
