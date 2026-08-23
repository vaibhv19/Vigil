/**
 * Vigil Dashboard — Vanilla JS Application
 * Fetches API data and dynamically renders run cards, detail views, and comparisons.
 */
(function () {
    'use strict';

    // --- DOM References ---
    const runsList = document.getElementById('runs-list');
    const runsLoader = document.getElementById('runs-loader');
    const viewRuns = document.getElementById('view-runs');
    const viewDetail = document.getElementById('view-run-detail');
    const viewCompare = document.getElementById('view-compare');
    const navRuns = document.getElementById('nav-runs');
    const navCompare = document.getElementById('nav-compare');
    const btnBackRuns = document.getElementById('btn-back-runs');
    const detailTitle = document.getElementById('detail-title');
    const detailMetrics = document.getElementById('detail-metrics');
    const tasksTbody = document.getElementById('tasks-tbody');
    const anomaliesList = document.getElementById('anomalies-list');
    const selectRunA = document.getElementById('select-run-a');
    const selectRunB = document.getElementById('select-run-b');
    const btnCompare = document.getElementById('btn-compare');
    const comparisonResults = document.getElementById('comparison-results');
    const toolsModal = document.getElementById('tools-modal');
    const toolsModalBody = document.getElementById('tools-modal-body');
    const btnCloseModal = document.getElementById('btn-close-modal');

    let cachedRuns = [];

    // --- Helpers ---
    function formatDate(isoStr) {
        if (!isoStr) return '—';
        const d = new Date(isoStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
            ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }

    function formatDuration(ms) {
        if (!ms) return '—';
        if (ms < 1000) return ms + 'ms';
        return (ms / 1000).toFixed(1) + 's';
    }

    function statusClass(status) {
        if (!status) return '';
        const s = status.toLowerCase();
        if (s === 'pass' || s === 'completed') return 'pass';
        if (s === 'fail' || s === 'failed') return 'fail';
        if (s === 'error') return 'error';
        if (s === 'running') return 'running';
        return '';
    }

    function deltaClass(value) {
        if (value > 0) return 'positive';
        if (value < 0) return 'negative';
        return 'neutral';
    }

    function deltaPrefix(value) {
        return value > 0 ? '+' : '';
    }

    // --- View Switching ---
    function switchView(viewName) {
        [viewRuns, viewDetail, viewCompare].forEach(v => {
            v.style.display = 'none';
            v.classList.remove('active');
        });
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));

        if (viewName === 'runs') {
            viewRuns.style.display = 'block';
            viewRuns.classList.add('active');
            navRuns.classList.add('active');
        } else if (viewName === 'detail') {
            viewDetail.style.display = 'block';
            viewDetail.classList.add('active');
        } else if (viewName === 'compare') {
            viewCompare.style.display = 'block';
            viewCompare.classList.add('active');
            navCompare.classList.add('active');
            populateRunSelectors();
        }
    }

    navRuns.addEventListener('click', () => switchView('runs'));
    navCompare.addEventListener('click', () => switchView('compare'));
    btnBackRuns.addEventListener('click', () => switchView('runs'));

    // --- Fetch Runs List ---
    async function loadRuns() {
        try {
            const res = await fetch('/api/runs');
            cachedRuns = await res.json();
            renderRunCards(cachedRuns);
        } catch (err) {
            runsList.innerHTML = '<div class="empty-state">Failed to load runs. Is the server running?</div>';
        }
    }

    function renderRunCards(runs) {
        runsLoader.style.display = 'none';
        if (runs.length === 0) {
            runsList.innerHTML = '<div class="empty-state">No evaluation runs found. Execute a suite to get started.</div>';
            return;
        }

        const frag = document.createDocumentFragment();
        runs.forEach(run => {
            const card = document.createElement('div');
            card.className = 'run-card';
            card.innerHTML = `
                <div class="run-card-header">
                    <span class="run-card-suite">${run.suite_name}</span>
                    <span class="run-card-version">${run.agent_version}</span>
                </div>
                <div class="run-card-meta">
                    <span>⏱ ${formatDuration(run.total_duration_ms)}</span>
                    <span>📅 ${formatDate(run.started_at)}</span>
                </div>
                <span class="status-badge ${statusClass(run.status)}">
                    <span class="status-dot"></span>
                    ${run.status}
                </span>
            `;
            card.addEventListener('click', () => loadRunDetail(run.id));
            frag.appendChild(card);
        });

        // Clear previous cards (but not the loader)
        runsList.querySelectorAll('.run-card').forEach(c => c.remove());
        runsList.appendChild(frag);
    }

    // --- Run Detail ---
    async function loadRunDetail(runId) {
        switchView('detail');
        detailTitle.textContent = 'Loading…';
        detailMetrics.innerHTML = '';
        tasksTbody.innerHTML = '';
        anomaliesList.innerHTML = '';

        try {
            const [detailRes, metricsRes, anomaliesRes] = await Promise.all([
                fetch(`/api/runs/${runId}`),
                fetch(`/api/metrics/runs/${runId}/summary`),
                fetch(`/api/runs/${runId}/anomalies`),
            ]);

            const detail = await detailRes.json();
            const metrics = await metricsRes.json();
            const anomalies = await anomaliesRes.json();

            detailTitle.textContent = `${detail.suite_name} — ${detail.agent_version}`;

            // Metrics Bar
            detailMetrics.innerHTML = `
                <div class="metric-card"><div class="metric-value">${metrics.pass_rate}%</div><div class="metric-label">Pass Rate</div></div>
                <div class="metric-card"><div class="metric-value">${metrics.total_tasks}</div><div class="metric-label">Total Tasks</div></div>
                <div class="metric-card"><div class="metric-value">${metrics.passed_tasks}</div><div class="metric-label">Passed</div></div>
                <div class="metric-card"><div class="metric-value">${metrics.failed_tasks}</div><div class="metric-label">Failed</div></div>
                <div class="metric-card"><div class="metric-value">${formatDuration(metrics.p50_latency_ms)}</div><div class="metric-label">P50 Latency</div></div>
                <div class="metric-card"><div class="metric-value">${formatDuration(metrics.p90_latency_ms)}</div><div class="metric-label">P90 Latency</div></div>
                <div class="metric-card"><div class="metric-value">${metrics.total_tool_calls}</div><div class="metric-label">Tool Calls</div></div>
                <div class="metric-card"><div class="metric-value">${metrics.total_anomalies}</div><div class="metric-label">Anomalies</div></div>
            `;

            // Task Results Table
            if (detail.task_results && detail.task_results.length > 0) {
                detail.task_results.forEach(tr => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${tr.task_id.substring(0, 8)}…</td>
                        <td><span class="status-badge ${statusClass(tr.status)}"><span class="status-dot"></span>${tr.status}</span></td>
                        <td>${tr.steps_taken ?? '—'}</td>
                        <td>${tr.final_output ? tr.final_output.substring(0, 60) + '…' : '—'}</td>
                        <td><button class="btn-tools" data-run-id="${runId}" data-result-id="${tr.id}">View</button></td>
                    `;
                    tasksTbody.appendChild(row);
                });
            } else {
                tasksTbody.innerHTML = '<tr><td colspan="5" class="empty-state">No task results.</td></tr>';
            }

            // Anomalies
            if (anomalies.length > 0) {
                anomalies.forEach(a => {
                    const el = document.createElement('div');
                    el.className = 'anomaly-card';
                    el.innerHTML = `
                        <div class="anomaly-type">${a.pattern_type} — ${a.severity}</div>
                        <div class="anomaly-detail">${JSON.stringify(a.incident_data)}</div>
                    `;
                    anomaliesList.appendChild(el);
                });
            } else {
                anomaliesList.innerHTML = '<div class="empty-state">No anomalies detected.</div>';
            }
        } catch (err) {
            detailTitle.textContent = 'Error loading run details';
        }
    }

    // --- Tool Calls Modal ---
    document.addEventListener('click', async (e) => {
        if (e.target.classList.contains('btn-tools')) {
            const runId = e.target.dataset.runId;
            const resultId = e.target.dataset.resultId;
            try {
                const res = await fetch(`/api/runs/${runId}/tasks/${resultId}/tools`);
                const tools = await res.json();
                renderToolsModal(tools);
            } catch (err) {
                toolsModalBody.innerHTML = '<div class="empty-state">Failed to load tool calls.</div>';
                toolsModal.style.display = 'flex';
            }
        }
    });

    function renderToolsModal(tools) {
        toolsModalBody.innerHTML = '';
        if (tools.length === 0) {
            toolsModalBody.innerHTML = '<div class="empty-state">No tool calls recorded.</div>';
        } else {
            tools.forEach(t => {
                const item = document.createElement('div');
                item.className = 'tool-call-item';
                item.innerHTML = `
                    <div class="tool-call-header">
                        <span class="tool-call-name">#${t.sequence_number} ${t.tool_name}</span>
                        <span class="tool-call-duration">${formatDuration(t.duration_ms)} · exit ${t.exit_code}</span>
                    </div>
                    <div class="tool-call-output">${t.stdout_capture || '(no output)'}</div>
                `;
                toolsModalBody.appendChild(item);
            });
        }
        toolsModal.style.display = 'flex';
    }

    btnCloseModal.addEventListener('click', () => { toolsModal.style.display = 'none'; });
    toolsModal.addEventListener('click', (e) => {
        if (e.target === toolsModal) toolsModal.style.display = 'none';
    });

    // --- Compare View ---
    function populateRunSelectors() {
        [selectRunA, selectRunB].forEach(sel => {
            sel.innerHTML = '<option value="">Select a run…</option>';
            cachedRuns.forEach(run => {
                const opt = document.createElement('option');
                opt.value = run.id;
                opt.textContent = `${run.suite_name} (${run.agent_version}) — ${formatDate(run.started_at)}`;
                sel.appendChild(opt);
            });
        });
    }

    btnCompare.addEventListener('click', async () => {
        const runA = selectRunA.value;
        const runB = selectRunB.value;
        if (!runA || !runB) {
            comparisonResults.innerHTML = '<div class="empty-state">Select two runs to compare.</div>';
            return;
        }
        if (runA === runB) {
            comparisonResults.innerHTML = '<div class="empty-state">Cannot compare a run with itself.</div>';
            return;
        }

        comparisonResults.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Comparing…</p></div>';

        try {
            const res = await fetch(`/api/metrics/compare?run_a=${runA}&run_b=${runB}`);
            const data = await res.json();
            renderComparison(data);
        } catch (err) {
            comparisonResults.innerHTML = '<div class="empty-state">Comparison failed.</div>';
        }
    });

    function renderComparison(data) {
        let html = `
            <div class="comparison-summary">
                <div class="delta-card">
                    <div class="delta-value ${deltaClass(data.pass_rate_delta)}">${deltaPrefix(data.pass_rate_delta)}${data.pass_rate_delta}%</div>
                    <div class="delta-label">Pass Rate Δ</div>
                </div>
                <div class="delta-card">
                    <div class="delta-value ${deltaClass(-data.p50_latency_delta_ms)}">${deltaPrefix(data.p50_latency_delta_ms)}${formatDuration(data.p50_latency_delta_ms)}</div>
                    <div class="delta-label">P50 Latency Δ</div>
                </div>
                <div class="delta-card">
                    <div class="delta-value ${deltaClass(-data.p90_latency_delta_ms)}">${deltaPrefix(data.p90_latency_delta_ms)}${formatDuration(data.p90_latency_delta_ms)}</div>
                    <div class="delta-label">P90 Latency Δ</div>
                </div>
                <div class="delta-card">
                    <div class="delta-value neutral">${data.total_tasks_a} → ${data.total_tasks_b}</div>
                    <div class="delta-label">Total Tasks</div>
                </div>
            </div>
        `;

        if (data.task_changes && data.task_changes.length > 0) {
            html += `
                <div class="task-results-table">
                    <h3>Task-Level Changes</h3>
                    <table>
                        <thead>
                            <tr><th>Task</th><th>Status Change</th><th>Latency Δ</th><th>Steps Δ</th><th>Anomaly Δ</th></tr>
                        </thead>
                        <tbody>
            `;
            data.task_changes.forEach(tc => {
                const isRegression = tc.status_change.includes('PASS -> FAIL');
                const isImproved = tc.status_change.includes('FAIL -> PASS');
                const rowClass = isRegression ? 'style="background: var(--accent-danger-bg)"' : isImproved ? 'style="background: var(--accent-success-bg)"' : '';
                html += `
                    <tr ${rowClass}>
                        <td>${tc.task_slug}</td>
                        <td>${tc.status_change}</td>
                        <td class="${deltaClass(-tc.latency_delta_ms)}">${deltaPrefix(tc.latency_delta_ms)}${formatDuration(tc.latency_delta_ms)}</td>
                        <td>${deltaPrefix(tc.steps_delta)}${tc.steps_delta}</td>
                        <td>${deltaPrefix(tc.anomaly_delta)}${tc.anomaly_delta}</td>
                    </tr>
                `;
            });
            html += '</tbody></table></div>';
        }

        comparisonResults.innerHTML = html;
    }

    // --- Init ---
    loadRuns();
})();
