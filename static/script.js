document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    
    // UI Elements
    const totalVal = document.getElementById('total-val');
    const targetVal = document.getElementById('target-val');
    const countdownVal = document.getElementById('countdown-val');
    const logText = document.getElementById('log-text');
    
    // Config Elements
    const urlInput = document.getElementById('url');
    const namesInput = document.getElementById('names');
    const areasInput = document.getElementById('areas');
    const loopToggle = document.getElementById('loop');

    function updateDashboard(data) {
        if (data.is_running) {
            startBtn.disabled = true;
        } else {
            startBtn.disabled = false;
        }
        
        totalVal.innerText = data.total_submissions;
        targetVal.innerText = data.current_name;
        
        // Format countdown to 00:XX
        const sec = data.countdown < 10 ? `0${data.countdown}` : data.countdown;
        countdownVal.innerText = `00:${sec}`;
        
        logText.innerText = data.logs.join('\n');
        
        // Auto scroll logs
        const logConsole = document.querySelector('.log-console');
        logConsole.scrollTop = logConsole.scrollHeight;
    }

    async function fetchStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            updateDashboard(data);
        } catch (err) {
            console.error("Error fetching status:", err);
        }
    }

    // Poll status every second
    setInterval(fetchStatus, 1000);

    startBtn.addEventListener('click', async () => {
        const payload = {
            url: urlInput.value,
            names: namesInput.value,
            areas: areasInput.value,
            loop: loopToggle.checked
        };
        
        try {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (!data.success) {
                alert(data.message);
            } else {
                fetchStatus();
            }
        } catch (err) {
            alert("Failed to start bot.");
            console.error(err);
        }
    });

    stopBtn.addEventListener('click', async () => {
        try {
            await fetch('/api/stop', { method: 'POST' });
            fetchStatus();
        } catch (err) {
            console.error(err);
        }
    });
});
