"""Telegram Notification Manager"""
import logging
from typing import List, Dict, Any
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler
from config import settings

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send notifications via Telegram Bot API"""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.application = None

    def send_signal_notification(self, signal: Dict[str, Any]):
        """Send signal notification"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot not configured")
            return

        try:
            bot = Bot(token=self.bot_token)

            # Format signal message
            message = self._format_signal_message(signal)

            # Send message
            bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )

            logger.info(f"Signal notification sent: {signal['type']} {signal['symbol']}")

        except Exception as e:
            logger.error(f"Failed to send signal notification: {e}")

    def send_position_update(self, position: Dict[str, Any]):
        """Send position update notification"""
        if not self.bot_token or not self.chat_id:
            return

        try:
            bot = Bot(token=self.bot_token)

            message = self._format_position_message(position)

            bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )

            logger.info(f"Position update sent: {position['ticket']}")

        except Exception as e:
            logger.error(f"Failed to send position notification: {e}")

    def send_trade_closed(self, trade: Dict[str, Any]):
        """Send trade closed notification"""
        if not self.bot_token or not self.chat_id:
            return

        try:
            bot = Bot(token=self.bot_token)

            message = self._format_trade_message(trade)

            bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )

            logger.info(f"Trade closed notification sent: {trade['ticket']}")

        except Exception as e:
            logger.error(f"Failed to send trade notification: {e}")

    def send_daily_summary(self, performance: Dict[str, Any]):
        """Send daily summary notification"""
        if not self.bot_token or not self.chat_id:
            return

        try:
            bot = Bot(token=self.bot_token)

            message = self._format_summary_message(performance)

            bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )

            logger.info("Daily summary notification sent")

        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")

    def send_risk_alert(self, risk_type: str, message: str):
        """Send risk alert notification"""
        if not self.bot_token or not self.chat_id:
            return

        try:
            bot = Bot(token=self.bot_token)

            risk_emoji = {
                "MAX_POSITION": "⚠️",
                "MAX_EXPOSURE": "⚠️",
                "MAX_DAILY_LOSS": "🚨",
                "MIN_RR": "⚠️"
            }

            emoji = risk_emoji.get(risk_type, "⚠️")

            bot.send_message(
                chat_id=self.chat_id,
                text=f"{emoji} RISK ALERT: {message}",
                parse_mode='HTML'
            )

            logger.warning(f"Risk alert sent: {risk_type}")

        except Exception as e:
            logger.error(f"Failed to send risk alert: {e}")

    def _format_signal_message(self, signal: Dict[str, Any]) -> str:
        """Format signal message"""
        type_emoji = "🟢" if signal['type'] == "BUY" else "🔴"
        confidence_color = "text-green-500" if signal['type'] == "BUY" else "text-red-500"

        message = f"""
📊 <b>EURUSD Signal ({signal['timeframe']})</b>
━━━━━━━━━━━━━━━━━━━━
{type_emoji} <b>Type: {signal['type']}</b>
{type_emoji} <b>Confidence: {signal['confidence']}%</b>
━━━━━━━━━━━━━━━━━━━━
<b>Entry:</b> {signal['entry']:.5f}
<b>SL:</b> {signal['sl']:.5f} | <b>TP:</b> {signal['tp']:.5f}
<b>RR:</b> 1:{signal['risk_reward']}
━━━━━━━━━━━━━━━━━━━━
<b>RSI:</b> {signal['indicators']['rsi']:.1f}
<b>MACD:</b> {signal['indicators']['macd']:.5f}
<b>EMA:</b> EMA9={signal['indicators']['ema_9']:.5f} | EMA21={signal['indicators']['ema_21']:.5f}
━━━━━━━━━━━━━━━━━━━━
<b>Reason:</b>
"""

        for reason in signal['reason']:
            message += f"• {reason}\n"

        return message

    def _format_position_message(self, position: Dict[str, Any]) -> str:
        """Format position message"""
        type_emoji = "🟢" if position['type'] == "BUY" else "🔴"
        pnl_color = "text-green-500" if position['pnl'] >= 0 else "text-red-500"

        message = f"""
📈 <b>Position Update</b>
━━━━━━━━━━━━━━━━━━━━
{type_emoji} <b>Symbol:</b> {position['symbol']}
{type_emoji} <b>Ticket:</b> {position['ticket']}
{type_emoji} <b>Type:</b> {position['type']}
{type_emoji} <b>Volume:</b> {position['volume']}
{type_emoji} <b>Entry:</b> {position['entry']:.5f}
{type_emoji} <b>Current:</b> {position['current']:.5f}
━━━━━━━━━━━━━━━━━━━━
<b>PnL:</b> {pnl_color}{position['pnl']:.2f}{pnl_color}
<b>Profit:</b> {position['profit']:.2f}
<b>Margin:</b> {position['margin']:.2f}
━━━━━━━━━━━━━━━━━━━━
<b>SL:</b> {position['sl']:.5f} | <b>TP:</b> {position['tp']:.5f}
━━━━━━━━━━━━━━━━━━━━
"""

        return message

    def _format_trade_message(self, trade: Dict[str, Any]) -> str:
        """Format trade closed message"""
        type_emoji = "🟢" if trade['type'] == "BUY" else "🔴"
        pnl_color = "text-green-500" if trade['pnl'] >= 0 else "text-red-500"

        message = f"""
✅ <b>Trade Closed</b>
━━━━━━━━━━━━━━━━━━━━
{type_emoji} <b>Ticket:</b> {trade['ticket']}
{type_emoji} <b>Symbol:</b> {trade['symbol']}
{type_emoji} <b>Type:</b> {trade['type']}
━━━━━━━━━━━━━━━━━━━━
<b>Entry:</b> {trade['entry']:.5f}
<b>Exit:</b> {trade['exit']:.5f}
━━━━━━━━━━━━━━━━━━━━
<b>PnL:</b> {pnl_color}{trade['pnl']:.2f}{pnl_color}
<b>Fees:</b> {trade['fees']:.2f}
━━━━━━━━━━━━━━━━━━━━
<b>Time:</b> {trade['close_time']}
━━━━━━━━━━━━━━━━━━━━
"""

        return message

    def _format_summary_message(self, performance: Dict[str, Any]) -> str:
        """Format daily summary message"""
        win_rate = performance.get('win_rate', 0)

        message = f"""
📊 <b>Daily Performance Summary</b>
━━━━━━━━━━━━━━━━━━━━
<b>Total Trades:</b> {performance['total_trades']}
<b>Win:</b> {performance['win_trades']} | <b>Loss:</b> {performance['loss_trades']}
<b>Win Rate:</b> {win_rate:.1f}%
━━━━━━━━━━━━━━━━━━━━
<b>Total PnL:</b> {performance['total_pnl']:.2f}
<b>Max Profit:</b> {performance['max_profit']:.2f}
<b>Max Drawdown:</b> {performance['max_drawdown']:.2f}
━━━━━━━━━━━━━━━━━━━━
<b>Avg RR:</b> {performance['avg_risk_reward']:.2f}
━━━━━━━━━━━━━━━━━━━━
"""

        return message

    def start_bot(self):
        """Start Telegram bot (outbound only for stability)"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot not configured, skipping startup")
            return
        
        logger.info("📱 Telegram notifier ready (Outbound messages only)")

    async def _start_command(self, update, context):
        """Handle /start command"""
        await update.message.reply_text(
            "Welcome to AI Trading Bot!\n\n"
            "Commands:\n"
            "/start - Start bot\n"
            "/help - Show help\n"
            "/status - Show status"
        )

    async def _help_command(self, update, context):
        """Handle /help command"""
        await update.message.reply_text(
            "AI Trading Bot - Help\n\n"
            "This bot sends trading signals, position updates, and trade notifications.\n\n"
            "Commands:\n"
            "/start - Start bot\n"
            "/help - Show this help\n"
            "/status - Show bot status"
        )

    async def _status_command(self, update, context):
        """Handle /status command"""
        await update.message.reply_text(
            "Bot is running!\n\n"
            "You will receive:\n"
            "- New signals\n"
            "- Position updates\n"
            "- Trade closed notifications\n"
            "- Daily summary\n"
            "- Risk alerts"
        )


# Singleton instance
telegram_notifier = TelegramNotifier()
