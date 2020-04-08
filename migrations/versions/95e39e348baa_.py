"""empty message

Revision ID: 95e39e348baa
Revises: addcbcee4c2c
Create Date: 2020-04-08 19:11:21.888556

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95e39e348baa'
down_revision = 'addcbcee4c2c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Show')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Show',
    sa.Column('venue_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('artist_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('start_time', sa.DATE(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['artist_id'], ['Artist.id'], name='Show_artist_id_fkey'),
    sa.ForeignKeyConstraint(['venue_id'], ['Venue.id'], name='Show_venue_id_fkey'),
    sa.PrimaryKeyConstraint('venue_id', 'artist_id', name='Show_pkey')
    )
    # ### end Alembic commands ###
