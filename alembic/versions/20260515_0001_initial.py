"""Initial schema

Revision ID: 20260515_0001
Revises:
Create Date: 2026-05-15 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260515_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("language_code", sa.String(length=12), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("referral_code", sa.String(length=32), nullable=True),
        sa.Column("referred_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
        sa.UniqueConstraint("referral_code", name="uq_users_referral_code"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=False)

    op.create_table(
        "tracked_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("affiliate_url", sa.Text(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="INR"),
        sa.Column("current_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("original_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("lowest_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("highest_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("check_interval_minutes", sa.BigInteger(), nullable=False, server_default="30"),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_tracked_products_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_tracked_products"),
        sa.UniqueConstraint("user_id", "canonical_url", name="uq_user_canonical_url"),
    )
    op.create_index("ix_tracked_products_user_id", "tracked_products", ["user_id"], unique=False)
    op.create_index("ix_tracked_products_next_check", "tracked_products", ["next_check_at", "status"], unique=False)
    op.create_index("ix_tracked_products_platform", "tracked_products", ["platform"], unique=False)

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tracked_product_id", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=True),
        sa.Column("original_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("scrape_strategy", sa.String(length=32), nullable=False),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["tracked_product_id"],
            ["tracked_products.id"],
            name="fk_price_history_tracked_product_id_tracked_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_price_history"),
    )
    op.create_index("ix_price_history_product_checked", "price_history", ["tracked_product_id", "checked_at"], unique=False)

    op.create_table(
        "affiliate_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tracked_product_id", sa.Integer(), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("affiliate_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.String(length=512), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["tracked_product_id"],
            ["tracked_products.id"],
            name="fk_affiliate_links_tracked_product_id_tracked_products",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_affiliate_links"),
    )
    op.create_index("ix_affiliate_links_status", "affiliate_links", ["status"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tracked_product_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(length=32), nullable=False),
        sa.Column("old_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("new_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("telegram_message_id", sa.Integer(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tracked_product_id"], ["tracked_products.id"], name="fk_notifications_tracked_product_id_tracked_products", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_notifications_user_id_users", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_notifications"),
    )
    op.create_index("ix_notifications_user_type", "notifications", ["user_id", "notification_type"], unique=False)

    op.create_table(
        "admin_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("event", sa.String(length=128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_admin_logs"),
    )
    op.create_index("ix_admin_logs_event", "admin_logs", ["event"], unique=False)
    op.create_index("ix_admin_logs_level", "admin_logs", ["level"], unique=False)

    op.create_table(
        "failed_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_failed_jobs"),
    )
    op.create_index("ix_failed_jobs_job", "failed_jobs", ["job_name", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_failed_jobs_job", table_name="failed_jobs")
    op.drop_table("failed_jobs")

    op.drop_index("ix_admin_logs_level", table_name="admin_logs")
    op.drop_index("ix_admin_logs_event", table_name="admin_logs")
    op.drop_table("admin_logs")

    op.drop_index("ix_notifications_user_type", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_affiliate_links_status", table_name="affiliate_links")
    op.drop_table("affiliate_links")

    op.drop_index("ix_price_history_product_checked", table_name="price_history")
    op.drop_table("price_history")

    op.drop_index("ix_tracked_products_platform", table_name="tracked_products")
    op.drop_index("ix_tracked_products_next_check", table_name="tracked_products")
    op.drop_index("ix_tracked_products_user_id", table_name="tracked_products")
    op.drop_table("tracked_products")

    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
