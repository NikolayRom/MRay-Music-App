"""add_gin_index_for_track_title

Revision ID: 1fe53648ef19
Revises: 3055c8acff53
Create Date: 2026-05-07 17:27:16.773658

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "1fe53648ef19"
down_revision: Union[str, Sequence[str], None] = "3055c8acff53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    op.create_index(
        'idx_track_title_trgm',
        'tracks',
        ['title'],
        postgresql_using='gin',
        postgresql_ops={'title': 'gin_trgm_ops'}
    )

def downgrade() -> None:
    op.drop_index('idx_track_title_trgm', table_name='tracks')
