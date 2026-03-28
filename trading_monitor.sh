#!/bin/bash
# Monitor Production Trading System
# Shows real-time status and logs

SERVICE_NAME="johntrading"

if [ "$1" = "-f" ] || [ "$1" = "--follow" ]; then
    # Follow logs in real time
    echo "Following logs (Press Ctrl+C to stop)..."
    echo ""
    journalctl -u $SERVICE_NAME -f
    
elif [ "$1" = "-s" ] || [ "$1" = "--status" ]; then
    # Show service status
    echo "Service Status:"
    echo "=============="
    systemctl status $SERVICE_NAME
    
elif [ "$1" = "-l" ] || [ "$1" = "--logs" ]; then
    # Show last 50 lines
    if [ -z "$2" ]; then
        LINES=50
    else
        LINES=$2
    fi
    echo "Last $LINES log lines:"
    journalctl -u $SERVICE_NAME -n $LINES
    
elif [ "$1" = "-t" ] || [ "$1" = "--today" ]; then
    # Show today's logs
    echo "Today's logs:"
    journalctl -u $SERVICE_NAME --since today
    
elif [ "$1" = "-p" ] || [ "$1" = "--process" ]; then
    # Show process info
    echo "Process Information:"
    ps aux | grep run_phase9
    echo ""
    echo "Network connections:"
    netstat -tulpn 2>/dev/null | grep python || ss -tulpn 2>/dev/null | grep python || echo "Network monitoring requires sudo"
    
elif [ "$1" = "--restart" ]; then
    # Restart service
    echo "Restarting trading service..."
    sudo systemctl restart $SERVICE_NAME
    sleep 2
    echo "Service restarted."
    systemctl status $SERVICE_NAME
    
elif [ "$1" = "--stop" ]; then
    # Stop service
    echo "Stopping trading service..."
    sudo systemctl stop $SERVICE_NAME
    echo "Service stopped."
    
elif [ "$1" = "--start" ]; then
    # Start service
    echo "Starting trading service..."
    sudo systemctl start $SERVICE_NAME
    sleep 2
    echo "Service started."
    systemctl status $SERVICE_NAME
    
elif [ "$1" = "--enable" ]; then
    # Enable auto-start on boot
    echo "Enabling auto-start on boot..."
    sudo systemctl enable $SERVICE_NAME
    echo "Auto-start enabled."
    
elif [ "$1" = "--disable" ]; then
    # Disable auto-start
    echo "Disabling auto-start..."
    sudo systemctl disable $SERVICE_NAME
    echo "Auto-start disabled."
    
else
    # Show help
    echo "Trading System Monitor & Control"
    echo "================================"
    echo ""
    echo "Usage: ./trading_monitor.sh [COMMAND]"
    echo ""
    echo "Monitoring:"
    echo "  -f, --follow      Follow logs in real-time"
    echo "  -s, --status      Show service status"
    echo "  -l, --logs [N]    Show last N log lines (default 50)"
    echo "  -t, --today       Show today's logs"
    echo "  -p, --process     Show process and network info"
    echo ""
    echo "Control:"
    echo "  --start           Start trading service"
    echo "  --stop            Stop trading service"
    echo "  --restart         Restart trading service"
    echo "  --enable          Enable auto-start on boot"
    echo "  --disable         Disable auto-start"
    echo ""
    echo "Examples:"
    echo "  ./trading_monitor.sh -f          # Watch logs"
    echo "  ./trading_monitor.sh --status    # Check status"
    echo "  ./trading_monitor.sh --restart   # Restart service"
    echo ""
fi
