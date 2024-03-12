"""favorite model added

Revision ID: 5444bd43f80d
Revises: 31625d9815bb
Create Date: 2024-03-12 06:00:07.015761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5444bd43f80d'
down_revision: Union[str, None] = '31625d9815bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('favorites',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('owner_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('associations_post_favorite',
    sa.Column('post_id', sa.String(), nullable=False),
    sa.Column('favorite_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['favorite_id'], ['favorites.id'], ),
    sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ),
    sa.PrimaryKeyConstraint('post_id', 'favorite_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('associations_post_favorite')
    op.drop_table('favorites')
    # ### end Alembic commands ###
