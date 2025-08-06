let refreshInterval;
let isAutoRefreshing = false;
let savedScrollPosition = 0;

/**
 * Renders the JSON data into the dashboard
 * @param {Object} data - The test results data
 */
function renderFromJson(data) {
    // Update summary section with test execution details
    document.getElementById('current-status').textContent = data.status || '';
    document.getElementById('start-time').textContent = data.start_time || '';
    
    // Only show end time when tests are completed
    const endTimeElement = document.getElementById('end-time');
    if (data.status === "Completed" && data.end_time) {
        endTimeElement.textContent = data.end_time;
        endTimeElement.style.color = '#0059a1';
    } else {
        endTimeElement.textContent = 'Running...';
        endTimeElement.style.color = '#e86b31';
    }
    
    // Update overall execution time with better formatting
    const overallTimeElement = document.getElementById('overall-time');
    if (data.status === "Completed") {
        overallTimeElement.textContent = data.overall_time;
        overallTimeElement.style.color = '#0059a1';
        overallTimeElement.style.fontWeight = 'bold';
    } else {
        overallTimeElement.textContent = data.overall_time || 'Calculating...';
        overallTimeElement.style.color = '#e86b31';
        overallTimeElement.style.fontWeight = 'normal';
    }
    
    document.getElementById('passed-count').textContent = data.passed;
    document.getElementById('failed-count').textContent = data.failed;
    document.getElementById('error-count').textContent = data.error || 0;
    document.getElementById('skipped-count').textContent = data.skipped;
    document.getElementById('inprogress-count').textContent = data.inprogress;
    document.getElementById('not-tested-count').textContent = data.not_tested || 0;

    // Store current scroll position before destroying table
    let currentScrollTop = 0;
    const scrollBody = $('.dataTables_scrollBody');
    if (scrollBody.length) {
        currentScrollTop = scrollBody.scrollTop();
    }

    // Generate table rows for each test case
    let tbody = '';
    data.tests.forEach((test, idx) => {
        // Create row with appropriate status class
        let statusClass = test.status?.toLowerCase().replace(' ', '').replace('not', 'not-');
        
        // Generate marker tags
        const markerTags = (test.markers || []).map(marker => 
            `<span class="marker-tag ${marker}">${marker}</span>`
        ).join(' ');
        
        // Format execution time display
        let executionTimeDisplay = test.execution_time || '';
        if (test.status === "In Progress") {
            executionTimeDisplay = 'Running...';
        } else if (test.status === "Not Started") {
            executionTimeDisplay = 'Pending';
        } else if (test.status === "Not Tested") {
            executionTimeDisplay = 'N/A';
        }
        
        // Main test row
        tbody += `<tr class="${statusClass}" data-test-idx="${idx}">
            <td class="${(test.status === 'Failed' || test.status === 'Error') && test.exception_log ? 'expandable' : ''}" data-idx="${idx}">
                ${test.name}
                ${(test.status === 'Failed' || test.status === 'Error') && test.exception_log ? '<span>▼ Click to view error</span>' : ''}
            </td>
            <td>${test.status}</td>
            <td><div class="test-markers">${markerTags}</div></td>
            <td>${test.start_time || ''}</td>
            <td>${test.end_time || ''}</td>
            <td>${executionTimeDisplay}</td>
        </tr>`;
    });
    
    // Check if DataTable exists and destroy it properly
    if ($.fn.DataTable.isDataTable('#test-table')) {
        $('#test-table').DataTable().destroy();
    }
    
    // Update table body with new rows BEFORE initializing DataTable
    $('#test-table tbody').html(tbody);

    // Initialize DataTable with the updated content
    $('#test-table').DataTable({
        order: [[0, 'asc']],
        pageLength: 100,
        lengthMenu: [10, 25, 50, 100, -1],
        scrollY: '600px',
        scrollCollapse: true,
        paging: false,
        columnDefs: [{
            targets: 0,
            type: 'natural',
            render: function(data, type, row) {
                if (type === 'sort') {
                    // Extract the number from test_case_X
                    const match = data.match(/test_(\w+)_(\d+)/);
                    if (match) {
                        const marker = match[1];
                        const num = parseInt(match[2]);
                        return `${marker}_${num.toString().padStart(3, '0')}`;
                    }
                    return data;
                }
                return data;
            }
        }],
        initComplete: function() {
            // Restore scroll position after table is fully initialized
            restoreScrollPosition();
        }
    });

    // Add click handlers for expandable error logs AFTER DataTable is initialized
    $('.expandable').off('click').on('click', function() {
        const idx = $(this).data('idx');
        const test = data.tests[idx];
        const currentRow = $(this).closest('tr');
        
        // Check if exception display already exists after this row
        let existingException = currentRow.next('.exception-display-row');
        
        if (existingException.length) {
            // If it exists, remove it
            existingException.remove();
            $(this).find('span').text('▼ Click to view error');
        } else {
            // Remove any other open exception displays
            $('.exception-display-row').remove();
            $('.expandable span').text('▼ Click to view error');
            
            // Escape HTML and preserve formatting
            const escapedLog = test.exception_log
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
            
            // Create the exception display as a table row
            const exceptionRow = $(`
                <tr class="exception-display-row">
                    <td colspan="6" style="padding: 0; background-color: #fff5f5; border: none;">
                        <div class="exception-display">
                            <div class="exception-content">
                                <strong>Exception Details for ${test.name}:</strong>
                                <button class="close-exception" onclick="closeException(${idx})">×</button>
                                <div class="exception-log">${escapedLog}</div>
                            </div>
                        </div>
                    </td>
                </tr>
            `);
            
            // Insert after the current row
            currentRow.after(exceptionRow);
            $(this).find('span').text('▲ Click to hide error');
        }
    });
}

/**
 * Fetches and loads the latest results
 */
function loadResults() {
    // Save current scroll position before refreshing
    saveScrollPosition();
    
    // Use relative path for Python HTTP server
    fetch('./results.json?' + new Date().getTime()) // Add timestamp to prevent caching
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderFromJson(data);
            
            // Restore scroll position after rendering
            restoreScrollPosition();
            
            // Stop auto-refresh if tests are completed
            if (data.status === "Completed" && isAutoRefreshing) {
                stopAutoRefresh();
                document.getElementById('refresh-status').textContent = 'Test execution completed!';
            }
        })
        .catch(err => {
            console.error('Error loading results:', err);
            document.getElementById('refresh-status').textContent = 'Error loading results: ' + err.message;
        });
}

/**
 * Start auto-refreshing every 5 seconds
 */
function startAutoRefresh() {
    if (!isAutoRefreshing) {
        isAutoRefreshing = true;
        refreshInterval = setInterval(loadResults, 5000);
        document.getElementById('refresh-status').textContent = 'Auto-refreshing every 5 seconds...';
        document.getElementById('refresh-btn').textContent = 'Stop Auto-Refresh';
    }
}

/**
 * Stop auto-refreshing
 */
function stopAutoRefresh() {
    if (isAutoRefreshing) {
        isAutoRefreshing = false;
        clearInterval(refreshInterval);
        document.getElementById('refresh-status').textContent = 'Auto-refresh stopped';
        document.getElementById('refresh-btn').textContent = 'Start Auto-Refresh';
    }
}

/**
 * Toggle auto-refresh on/off
 */
function toggleAutoRefresh() {
    if (isAutoRefreshing) {
        stopAutoRefresh();
    } else {
        startAutoRefresh();
    }
}

/**
 * Stop the test execution by creating a stop signal file
 */
function stopTestExecution() {
    // Create a blob with stop signal
    const stopSignal = new Blob(['stop'], { type: 'text/plain' });
    
    // Create a download link to save the stop file
    const link = document.createElement('a');
    link.href = URL.createObjectURL(stopSignal);
    link.download = 'stop_tests.txt';
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Update status
    document.getElementById('refresh-status').textContent = 'Stop signal created - save as stop_tests.txt in your project folder';
    document.getElementById('refresh-status').style.color = '#dc3545';
}

/**
 * Save current scroll position
 */
function saveScrollPosition() {
    const scrollBody = $('.dataTables_scrollBody');
    if (scrollBody.length) {
        savedScrollPosition = scrollBody.scrollTop();
    }
}

/**
 * Restore saved scroll position
 */
function restoreScrollPosition() {
    setTimeout(() => {
        const scrollBody = $('.dataTables_scrollBody');
        if (scrollBody.length && savedScrollPosition > 0) {
            scrollBody.scrollTop(savedScrollPosition);
        }
    }, 150);
}

/**
 * Close exception display
 * @param {number} idx - Test index
 */
function closeException(idx) {
    $('.exception-display-row').remove();
    $('.expandable span').text('▼ Click to view error');
}

/**
 * Initialize dashboard when DOM is ready
 */
$(document).ready(function() {
    // Initial data load
    loadResults();
    
    console.log('MIST Automation Dashboard initialized');
});