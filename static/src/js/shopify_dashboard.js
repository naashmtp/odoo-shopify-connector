/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ShopifyDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            loading: true,
            stats: {
                total_orders: 0,
                orders_today: 0,
                total_products: 0,
                sync_products: 0,
                total_customers: 0,
                pending_queue: 0,
                failed_jobs: 0,
                total_revenue: 0,
            },
            instances: [],
            recent_orders: [],
            recent_logs: [],
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.startAutoRefresh();
        });
    }

    async loadDashboardData() {
        try {
            this.state.loading = true;

            const [stats, instances, orders, logs] = await Promise.all([
                this.orm.call("shopify.instance", "get_dashboard_stats", []),
                this.orm.searchRead("shopify.instance", [["active", "=", true]], ["name", "shop_url", "state"]),
                this.orm.searchRead(
                    "shopify.order",
                    [],
                    ["name", "order_date", "total_price", "financial_status", "fulfillment_status"],
                    { limit: 10, order: "order_date desc" }
                ),
                this.orm.searchRead(
                    "shopify.log",
                    [],
                    ["message", "level", "create_date", "model_name"],
                    { limit: 10, order: "create_date desc" }
                ),
            ]);

            this.state.stats = stats;
            this.state.instances = instances;
            this.state.recent_orders = orders;
            this.state.recent_logs = logs;
        } catch (error) {
            console.error("Error loading dashboard data:", error);
        } finally {
            this.state.loading = false;
        }
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 30000); // Refresh every 30 seconds
    }

    willUnmount() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }

    async openOrders() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "shopify.order",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async openProducts() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "shopify.product",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async openQueue() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "shopify.queue",
            domain: [["state", "=", "pending"]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async openLogs() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "shopify.log",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async syncNow(instanceId) {
        try {
            await this.orm.call("shopify.instance", "action_sync_all", [instanceId]);
            await this.loadDashboardData();
        } catch (error) {
            console.error("Sync error:", error);
        }
    }

    getStatusClass(state) {
        const stateMap = {
            'connected': 'success',
            'disconnected': 'danger',
            'draft': 'secondary',
        };
        return stateMap[state] || 'info';
    }

    getLogLevelClass(level) {
        const levelMap = {
            'error': 'danger',
            'warning': 'warning',
            'info': 'info',
            'debug': 'secondary',
        };
        return levelMap[level] || 'info';
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount || 0);
    }

    formatDate(date) {
        if (!date) return '';
        return new Date(date).toLocaleString('fr-FR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

ShopifyDashboard.template = "shopify_integration.Dashboard";

registry.category("actions").add("shopify_dashboard", ShopifyDashboard);