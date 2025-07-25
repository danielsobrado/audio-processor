"""Make hashed_password nullable for JIT provisioning

Revision ID: 148d0033867d
Revises:
Create Date: 2025-07-08 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "148d0033867d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("users", "hashed_password", existing_type=sa.VARCHAR(), nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column("users", "hashed_password", existing_type=sa.VARCHAR(), nullable=False)
    # ### end Alembic commands ###
