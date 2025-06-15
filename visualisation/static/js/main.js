document.addEventListener('DOMContentLoaded', function() {
    // Navigation handling
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    const sections = document.querySelectorAll('.section-container');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Show the selected section, hide others
            const sectionId = this.getAttribute('data-section');
            sections.forEach(section => {
                section.classList.add('d-none');
                if (section.id === `${sectionId}-section`) {
                    section.classList.remove('d-none');
                }
            });
            
            // Load section-specific data
            if (sectionId === 'comparison') {
                loadComparisonFiles();
            } else if (sectionId === 'tariff') {
                loadTariffImpactData();
            } else if (sectionId === 'custom') {
                loadCustomFilesDropdown();
            }
        });
    });
    
    // ================= OVERVIEW SECTION =================
    
    // Coin & File Selection
    const coinSelect = document.getElementById('coin-select');
    const fileSelect = document.getElementById('file-select');
    
    coinSelect.addEventListener('change', function() {
        const selectedCoin = this.value;
        fileSelect.innerHTML = '<option value="">Loading files...</option>';
        
        if (selectedCoin) {
            fetch('/api/available_files')
                .then(response => response.json())
                .then(data => {
                    const coinFiles = data[selectedCoin] || [];
                    fileSelect.innerHTML = '';
                    
                    if (coinFiles.length === 0) {
                        fileSelect.innerHTML = '<option value="">No files available</option>';
                    } else {
                        coinFiles.forEach(file => {
                            const option = document.createElement('option');
                            option.value = file;
                            option.textContent = file;
                            fileSelect.appendChild(option);
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching files:', error);
                    fileSelect.innerHTML = '<option value="">Error loading files</option>';
                });
        } else {
            fileSelect.innerHTML = '<option value="">Select a coin first</option>';
        }
    });
    
    // File selection change handler
    fileSelect.addEventListener('change', function() {
        const selectedFile = this.value;
        
        if (selectedFile) {
            // Fetch file metadata
            fetch(`/api/file_metadata/${selectedFile}`)
                .then(response => response.json())
                .then(data => {
                    // Display file details
                    const fileDetails = document.getElementById('file-details');
                    fileDetails.innerHTML = `
                        <p><strong>Coin:</strong> ${data.coin}</p>
                        <p><strong>Timeframe:</strong> ${data.timeframe}</p>
                        <p><strong>Date Range:</strong> ${data.date_range}</p>
                        <p><strong>Data Points:</strong> ${data.num_rows}</p>
                        <p><strong>Size:</strong> ${data.file_size_kb} KB</p>
                    `;
                    
                    // Load the file data and render charts
                    loadFileData(selectedFile);
                })
                .catch(error => {
                    console.error('Error fetching file metadata:', error);
                    document.getElementById('file-details').innerHTML = '<p class="text-danger">Error loading file details</p>';
                });
        } else {
            document.getElementById('file-details').innerHTML = '<p class="text-muted">No file selected</p>';
        }
    });
    
    // Function to load and display file data
    function loadFileData(filename) {
        // Display loading indicators
        document.getElementById('price-chart').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('volume-chart').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('metrics-display').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Fetch the actual data
        fetch(`/api/data/${filename}`)
            .then(response => response.json())
            .then(data => {
                // Render the price chart
                renderPriceChart(data, filename);
                
                // Render the volume chart
                renderVolumeChart(data, filename);
                
                // Calculate and display metrics
                fetch(`/api/calculate_metrics/${filename}`)
                    .then(response => response.json())
                    .then(metrics => {
                        renderMetrics(metrics);
                    })
                    .catch(error => {
                        console.error('Error fetching metrics:', error);
                        document.getElementById('metrics-display').innerHTML = '<p class="text-danger">Error calculating metrics</p>';
                    });
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                document.getElementById('price-chart').innerHTML = '<p class="text-danger">Error loading chart data</p>';
                document.getElementById('volume-chart').innerHTML = '<p class="text-danger">Error loading volume data</p>';
            });
    }
    
    // Function to render price chart
    function renderPriceChart(data, filename) {
        // Extract coin and timeframe from filename
        const parts = filename.split('_');
        const coin = parts[0];
        const timeframe = parts[1] || '';
        
        // Prepare data for ApexCharts
        const chartData = data.map(item => ({
            x: new Date(item.date),
            y: [
                parseFloat(item.open),
                parseFloat(item.high),
                parseFloat(item.low),
                parseFloat(item.close)
            ]
        }));
        
        // Configure chart options
        const options = {
            series: [{
                name: `${coin} Price`,
                data: chartData
            }],
            chart: {
                type: 'candlestick',
                height: 350,
                toolbar: {
                    show: true
                }
            },
            title: {
                text: `${coin} Price (${timeframe})`,
                align: 'left'
            },
            xaxis: {
                type: 'datetime',
                labels: {
                    datetimeUTC: false
                }
            },
            yaxis: {
                tooltip: {
                    enabled: true
                },
                labels: {
                    formatter: function(value) {
                        return value.toFixed(2);
                    }
                }
            },
            tooltip: {
                enabled: true
            }
        };
        
        // Clear the container and create chart
        document.getElementById('price-chart').innerHTML = '';
        const chart = new ApexCharts(document.getElementById('price-chart'), options);
        chart.render();
    }
    
    // Function to render volume chart
    function renderVolumeChart(data, filename) {
        // Extract coin and timeframe from filename
        const parts = filename.split('_');
        const coin = parts[0];
        const timeframe = parts[1] || '';
        
        // Prepare data for ApexCharts
        const chartData = data.map(item => ({
            x: new Date(item.date),
            y: parseFloat(item.volume)
        }));
        
        // Configure chart options
        const options = {
            series: [{
                name: `${coin} Volume`,
                data: chartData
            }],
            chart: {
                type: 'bar',
                height: 250,
                toolbar: {
                    show: true
                }
            },
            title: {
                text: `${coin} Trading Volume (${timeframe})`,
                align: 'left'
            },
            xaxis: {
                type: 'datetime',
                labels: {
                    datetimeUTC: false
                }
            },
            yaxis: {
                labels: {
                    formatter: function(value) {
                        if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
                        if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
                        return value.toFixed(0);
                    }
                }
            },
            colors: ['#00E396']
        };
        
        // Clear the container and create chart
        document.getElementById('volume-chart').innerHTML = '';
        const chart = new ApexCharts(document.getElementById('volume-chart'), options);
        chart.render();
    }
    
    // Function to render metrics
    function renderMetrics(metrics) {
        const metricsDisplay = document.getElementById('metrics-display');
        
        // Format numbers for display
        const formatNumber = (num, decimals = 2) => {
            if (isNaN(num)) return 'N/A';
            return parseFloat(num).toFixed(decimals);
        };
        
        // Format percentages
        const formatPercent = (num) => {
            if (isNaN(num)) return 'N/A';
            const formatted = parseFloat(num).toFixed(2) + '%';
            return `<span class="${num >= 0 ? 'positive' : 'negative'}">${formatted}</span>`;
        };
        
        // Build HTML for metrics
        let html = `
            <div class="row">
                <div class="col-6 mb-3">
                    <div class="small-stat">
                        <h3>Avg. Price</h3>
                        <p>${formatNumber(metrics.avg_price)}</p>
                    </div>
                </div>
                <div class="col-6 mb-3">
                    <div class="small-stat">
                        <h3>Avg. Daily Return</h3>
                        <p>${formatPercent(metrics.avg_daily_return)}</p>
                    </div>
                </div>
                <div class="col-6 mb-3">
                    <div class="small-stat">
                        <h3>Volatility</h3>
                        <p>${formatPercent(metrics.price_volatility)}</p>
                    </div>
                </div>
                <div class="col-6 mb-3">
                    <div class="small-stat">
                        <h3>Max Drawdown</h3>
                        <p class="negative">${formatPercent(metrics.max_drawdown)}</p>
                    </div>
                </div>
                <div class="col-6 mb-3">
                    <div class="small-stat">
                        <h3>Sharpe Ratio</h3>
                        <p class="${metrics.sharpe_ratio >= 1 ? 'positive' : 'negative'}">${formatNumber(metrics.sharpe_ratio)}</p>
                    </div>
                </div>
                <div class="col-6 mb-3">
                    <div class="small-stat">
                        <h3>Avg. Volume</h3>
                        <p>${formatNumber(metrics.avg_volume, 0)}</p>
                    </div>
                </div>
            </div>
        `;
        
        metricsDisplay.innerHTML = html;
    }
    
    // ================= COMPARISON SECTION =================
    
    function loadComparisonFiles() {
        const comparisonFileSelector = document.getElementById('comparison-file-selector');
        comparisonFileSelector.innerHTML = '<p class="text-muted">Loading available files...</p>';
        
        fetch('/api/available_files')
            .then(response => response.json())
            .then(data => {
                let html = '';
                
                // Create a group of checkboxes for each coin
                for (const [coin, files] of Object.entries(data)) {
                    html += `<h6 class="mt-2">${coin}</h6>`;
                    
                    files.forEach(file => {
                        html += `
                            <div class="form-check">
                                <input class="form-check-input comparison-file-checkbox" type="checkbox" value="${file}" id="comp-${file.replace(/\./g, '-')}">
                                <label class="form-check-label" for="comp-${file.replace(/\./g, '-')}">
                                    ${file}
                                </label>
                            </div>
                        `;
                    });
                }
                
                comparisonFileSelector.innerHTML = html;
                
                // Add event listener for the compare button
                document.getElementById('run-comparison').addEventListener('click', runComparison);
            })
            .catch(error => {
                console.error('Error fetching files for comparison:', error);
                comparisonFileSelector.innerHTML = '<p class="text-danger">Error loading files</p>';
            });
    }
    
    function runComparison() {
        // Get selected files
        const checkboxes = document.querySelectorAll('.comparison-file-checkbox:checked');
        const selectedFiles = Array.from(checkboxes).map(cb => cb.value);
        
        if (selectedFiles.length === 0) {
            alert('Please select at least one file to compare');
            return;
        }
        
        // Get selected metric
        const metric = document.getElementById('metric-select').value;
        
        // Build query string
        const queryString = selectedFiles.map(file => `files=${encodeURIComponent(file)}`).join('&') + `&metric=${metric}`;
        
        // Show loading state
        document.getElementById('comparison-chart').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('comparison-table').innerHTML = '<tr><td colspan="8" class="text-center">Loading comparison data...</td></tr>';
        
        // Fetch comparison data
        fetch(`/api/comparison?${queryString}`)
            .then(response => response.json())
            .then(data => {
                renderComparisonChart(data, metric);
                renderComparisonTable(data);
            })
            .catch(error => {
                console.error('Error fetching comparison data:', error);
                document.getElementById('comparison-chart').innerHTML = '<p class="text-danger">Error loading comparison data</p>';
                document.getElementById('comparison-table').innerHTML = '<tr><td colspan="8" class="text-danger">Error loading comparison data</td></tr>';
            });
    }
    
    function renderComparisonChart(data, metric) {
        if (data.length === 0) {
            document.getElementById('comparison-chart').innerHTML = '<p class="text-center text-muted">No data available for comparison</p>';
            return;
        }
        
        // Prepare data for the chart
        const seriesData = [];
        
        // Group by coin
        const coinGroups = {};
        data.forEach(item => {
            if (!coinGroups[item.coin]) {
                coinGroups[item.coin] = [];
            }
            coinGroups[item.coin].push(item);
        });
        
        // Create a series for each coin
        for (const [coin, items] of Object.entries(coinGroups)) {
            let metricLabel = '';
            switch (metric) {
                case 'close':
                    metricLabel = 'Average Price';
                    break;
                case 'volume':
                    metricLabel = 'Average Volume';
                    break;
                case 'percent_change':
                    metricLabel = 'Percent Change';
                    break;
                default:
                    metricLabel = metric;
            }
            
            seriesData.push({
                name: `${coin} ${metricLabel}`,
                data: items.map(item => ({
                    x: item.filename.split('_').slice(1).join('_'), // Use filename without coin as label
                    y: metric === 'percent_change' ? item.percent_change : item.mean
                }))
            });
        }
        
        // Configure chart
        const options = {
            series: seriesData,
            chart: {
                type: 'bar',
                height: 350,
                toolbar: {
                    show: true
                },
                stacked: false
            },
            plotOptions: {
                bar: {
                    horizontal: false
                }
            },
            title: {
                text: `Comparison of ${metric === 'percent_change' ? 'Percent Change' : (metric === 'close' ? 'Average Price' : 'Average Volume')}`,
                align: 'left'
            },
            xaxis: {
                type: 'category',
                labels: {
                    rotate: -45,
                    rotateAlways: true
                }
            },
            yaxis: {
                title: {
                    text: metric === 'percent_change' ? 'Percent Change (%)' : (metric === 'close' ? 'Price' : 'Volume')
                },
                labels: {
                    formatter: function(value) {
                        if (metric === 'volume' && value >= 1000000) {
                            return (value / 1000000).toFixed(1) + 'M';
                        } else if (metric === 'volume' && value >= 1000) {
                            return (value / 1000).toFixed(1) + 'K';
                        } else if (metric === 'percent_change') {
                            return value.toFixed(2) + '%';
                        } else {
                            return value.toFixed(2);
                        }
                    }
                }
            },
            tooltip: {
                y: {
                    formatter: function(value) {
                        if (metric === 'volume' && value >= 1000000) {
                            return (value / 1000000).toFixed(2) + 'M';
                        } else if (metric === 'volume' && value >= 1000) {
                            return (value / 1000).toFixed(2) + 'K';
                        } else if (metric === 'percent_change') {
                            return value.toFixed(2) + '%';
                        } else {
                            return value.toFixed(4);
                        }
                    }
                }
            },
            colors: ['#008FFB', '#00E396', '#FEB019', '#FF4560', '#775DD0']
        };
        
        // Render chart
        document.getElementById('comparison-chart').innerHTML = '';
        const chart = new ApexCharts(document.getElementById('comparison-chart'), options);
        chart.render();
    }
    
    function renderComparisonTable(data) {
        if (data.length === 0) {
            document.getElementById('comparison-table').innerHTML = '<tr><td colspan="8" class="text-center">No data available for comparison</td></tr>';
            return;
        }
        
        const tableBody = document.createElement('tbody');
        
        // Format number for display
        const formatNum = (num, decimals = 2) => {
            if (isNaN(num)) return 'N/A';
            return parseFloat(num).toFixed(decimals);
        };
        
        // Create table rows
        data.forEach(item => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td>${item.coin}</td>
                <td>${item.filename.split('_').slice(1).join('_')}</td>
                <td>${formatNum(item.min)}</td>
                <td>${formatNum(item.max)}</td>
                <td>${formatNum(item.mean)}</td>
                <td>${formatNum(item.median)}</td>
                <td>${formatNum(item.std)}</td>
                <td class="${item.percent_change >= 0 ? 'positive' : 'negative'}">${formatNum(item.percent_change)}%</td>
            `;
            
            tableBody.appendChild(tr);
        });
        
        // Create table header
        const tableHead = document.createElement('thead');
        tableHead.innerHTML = `
            <tr>
                <th>Coin</th>
                <th>File</th>
                <th>Min</th>
                <th>Max</th>
                <th>Mean</th>
                <th>Median</th>
                <th>Standard Deviation</th>
                <th>% Change</th>
            </tr>
        `;
        
        // Replace table content
        const table = document.getElementById('comparison-table');
        table.innerHTML = '';
        table.appendChild(tableHead);
        table.appendChild(tableBody);
    }
    
    // ================= TARIFF IMPACT SECTION =================
    
    function loadTariffImpactData() {
        // Show loading indicators
        document.getElementById('tariff-impact-chart').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('volume-impact-chart').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('volatility-chart').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('tariff-impact-table').innerHTML = '<tr><td colspan="7" class="text-center">Loading impact data...</td></tr>';
        
        // Fetch tariff impact data
        fetch('/api/tariff_impact')
            .then(response => response.json())
            .then(data => {
                renderTariffImpactChart(data);
                renderVolumeImpactChart(data);
                renderVolatilityChart(data);
                renderImpactTable(data);
            })
            .catch(error => {
                console.error('Error fetching tariff impact data:', error);
                document.getElementById('tariff-impact-chart').innerHTML = '<p class="text-danger">Error loading impact data</p>';
                document.getElementById('volume-impact-chart').innerHTML = '<p class="text-danger">Error loading impact data</p>';
                document.getElementById('volatility-chart').innerHTML = '<p class="text-danger">Error loading impact data</p>';
                document.getElementById('tariff-impact-table').innerHTML = '<tr><td colspan="7" class="text-danger">Error loading impact data</td></tr>';
            });
    }
    
    function renderTariffImpactChart(data) {
        if (data.length === 0) {
            document.getElementById('tariff-impact-chart').innerHTML = '<p class="text-center text-muted">No impact data available</p>';
            return;
        }
        
        // Sort data by price change (most negative first)
        data.sort((a, b) => a.price_change_pct - b.price_change_pct);
        
        // Prepare chart data
        const seriesData = [
            {
                name: 'Pre-Tariff Average Price',
                data: data.map(item => item.pre_avg_price)
            },
            {
                name: 'Post-Tariff Average Price',
                data: data.map(item => item.post_avg_price)
            }
        ];
        
        // Configure chart
        const options = {
            series: seriesData,
            chart: {
                type: 'bar',
                height: 350,
                stacked: false,
                toolbar: {
                    show: true
                }
            },
            plotOptions: {
                bar: {
                    horizontal: false,
                    columnWidth: '55%',
                    endingShape: 'rounded'
                }
            },
            dataLabels: {
                enabled: false
            },
            stroke: {
                show: true,
                width: 2,
                colors: ['transparent']
            },
            title: {
                text: 'Price Impact of Trump Tariff Announcement',
                align: 'left'
            },
            xaxis: {
                categories: data.map(item => item.coin),
                title: {
                    text: 'Cryptocurrency'
                }
            },
            yaxis: {
                title: {
                    text: 'Price'
                },
                labels: {
                    formatter: function(value) {
                        return value.toFixed(2);
                    }
                }
            },
            fill: {
                opacity: 1
            },
            tooltip: {
                y: {
                    formatter: function(value) {
                        return value.toFixed(4);
                    }
                }
            },
            colors: ['#77B6EA', '#FF4560']
        };
        
        // Render chart
        document.getElementById('tariff-impact-chart').innerHTML = '';
        const chart = new ApexCharts(document.getElementById('tariff-impact-chart'), options);
        chart.render();
    }
    
    function renderVolumeImpactChart(data) {
        if (data.length === 0) {
            document.getElementById('volume-impact-chart').innerHTML = '<p class="text-center text-muted">No volume impact data available</p>';
            return;
        }
        
        // Sort data by volume change (highest first)
        data.sort((a, b) => b.volume_change_pct - a.volume_change_pct);
        
        // Prepare chart data
        const chartData = data.map(item => ({
            x: item.coin,
            y: item.volume_change_pct
        }));
        
        // Configure chart
        const options = {
            series: [{
                name: 'Volume Change',
                data: chartData
            }],
            chart: {
                type: 'bar',
                height: 300,
                toolbar: {
                    show: true
                }
            },
            plotOptions: {
                bar: {
                    borderRadius: 4,
                    horizontal: false,
                    columnWidth: '70%',
                    distributed: true
                }
            },
            dataLabels: {
                enabled: false
            },
            title: {
                text: 'Trading Volume Change After Tariff',
                align: 'left'
            },
            xaxis: {
                categories: data.map(item => item.coin),
                title: {
                    text: 'Cryptocurrency'
                }
            },
            yaxis: {
                title: {
                    text: 'Volume Change (%)'
                },
                labels: {
                    formatter: function(value) {
                        return value.toFixed(1) + '%';
                    }
                }
            },
            tooltip: {
                y: {
                    formatter: function(value) {
                        return value.toFixed(2) + '%';
                    }
                }
            },
            colors: data.map(item => item.volume_change_pct >= 0 ? '#00E396' : '#FF4560')
        };
        
        // Render chart
        document.getElementById('volume-impact-chart').innerHTML = '';
        const chart = new ApexCharts(document.getElementById('volume-impact-chart'), options);
        chart.render();
    }
    
    function renderVolatilityChart(data) {
        if (data.length === 0) {
            document.getElementById('volatility-chart').innerHTML = '<p class="text-center text-muted">No volatility data available</p>';
            return;
        }
        
        // For this chart, we'll use a radar chart to show multiple aspects of the impact
        const options = {
            series: data.map(item => ({
                name: item.coin,
                data: [
                    Math.abs(item.price_change_pct), // Price Impact (absolute value)
                    item.volume_change_pct,          // Volume Change
                    item.post_avg_price / item.pre_avg_price * 100 - 100 // Price Change %
                ]
            })),
            chart: {
                height: 300,
                type: 'radar',
                dropShadow: {
                    enabled: true,
                    blur: 1,
                    left: 1,
                    top: 1
                }
            },
            title: {
                text: 'Tariff Impact Analysis'
            },
            stroke: {
                width: 2
            },
            fill: {
                opacity: 0.1
            },
            markers: {
                size: 3,
                hover: {
                    size: 7
                }
            },
            xaxis: {
                categories: ['Price Impact', 'Volume Change', 'Price % Change']
            },
            yaxis: {
                labels: {
                    formatter: function(val) {
                        return val.toFixed(1) + '%';
                    }
                }
            },
            tooltip: {
                y: {
                    formatter: function(val) {
                        return val.toFixed(2) + '%';
                    }
                }
            }
        };
        
        // Render chart
        document.getElementById('volatility-chart').innerHTML = '';
        const chart = new ApexCharts(document.getElementById('volatility-chart'), options);
        chart.render();
    }
    
    function renderImpactTable(data) {
        if (data.length === 0) {
            document.getElementById('tariff-impact-table').innerHTML = '<tr><td colspan="7" class="text-center">No impact data available</td></tr>';
            return;
        }
        
        const tableBody = document.createElement('tbody');
        
        // Format number for display
        const formatNum = (num, decimals = 2) => {
            if (isNaN(num)) return 'N/A';
            return parseFloat(num).toFixed(decimals);
        };
        
        // Format percentage
        const formatPercent = (num) => {
            if (isNaN(num)) return 'N/A';
            return `<span class="${num >= 0 ? 'positive' : 'negative'}">${formatNum(num)}%</span>`;
        };
        
        // Create table rows
        data.forEach(item => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td>${item.coin}</td>
                <td>${formatNum(item.pre_avg_price)}</td>
                <td>${formatNum(item.post_avg_price)}</td>
                <td>${formatPercent(item.price_change_pct)}</td>
                <td>${formatNum(item.pre_avg_volume)}</td>
                <td>${formatNum(item.post_avg_volume)}</td>
                <td>${formatPercent(item.volume_change_pct)}</td>
            `;
            
            tableBody.appendChild(tr);
        });
        
        // Create table header
        const tableHead = document.createElement('thead');
        tableHead.innerHTML = `
            <tr>
                <th>Coin</th>
                <th>Pre-Tariff Avg. Price</th>
                <th>Post-Tariff Avg. Price</th>
                <th>Price Change %</th>
                <th>Pre-Tariff Avg. Volume</th>
                <th>Post-Tariff Avg. Volume</th>
                <th>Volume Change %</th>
            </tr>
        `;
        
        // Replace table content
        const table = document.getElementById('tariff-impact-table');
        table.innerHTML = '';
        table.appendChild(tableHead);
        table.appendChild(tableBody);
    }
    
    // ================= CUSTOM ANALYSIS SECTION =================
    
    function loadCustomFilesDropdown() {
        const fileSelect = document.getElementById('custom-file-select');
        fileSelect.innerHTML = '<option value="">Loading files...</option>';
        
        fetch('/api/available_files')
            .then(response => response.json())
            .then(data => {
                fileSelect.innerHTML = '<option value="">Select a file</option>';
                
                // Add all files to the dropdown
                for (const [coin, files] of Object.entries(data)) {
                    // Create an optgroup for each coin
                    const group = document.createElement('optgroup');
                    group.label = coin;
                    
                    files.forEach(file => {
                        const option = document.createElement('option');
                        option.value = file;
                        option.textContent = file;
                        group.appendChild(option);
                    });
                    
                    fileSelect.appendChild(group);
                }
                
                // Show/hide indicator parameters based on selection
                document.getElementById('indicator').addEventListener('change', function() {
                    const indicatorParams = document.querySelector('.indicator-params');
                    if (this.value === 'none') {
                        indicatorParams.classList.add('d-none');
                    } else {
                        indicatorParams.classList.remove('d-none');
                    }
                });
                
                // Add event listener for the generate button
                document.getElementById('generate-custom-chart').addEventListener('click', generateCustomChart);
            })
            .catch(error => {
                console.error('Error fetching files for custom analysis:', error);
                fileSelect.innerHTML = '<option value="">Error loading files</option>';
            });
    }
    
    function generateCustomChart() {
        const selectedFile = document.getElementById('custom-file-select').value;
        
        if (!selectedFile) {
            alert('Please select a data file');
            return;
        }
        
        const chartType = document.getElementById('chart-type').value;
        const yAxisData = document.getElementById('y-axis').value;
        const indicator = document.getElementById('indicator').value;
        const period = parseInt(document.getElementById('period').value) || 20;
        
        // Show loading state
        document.getElementById('custom-chart').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        document.getElementById('custom-analysis-results').innerHTML = '<div class="d-flex justify-content-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
        
        // Fetch the file data
        fetch(`/api/data/${selectedFile}`)
            .then(response => response.json())
            .then(data => {
                // Apply technical indicator if selected
                let indicatorData = [];
                if (indicator !== 'none') {
                    indicatorData = calculateIndicator(data, indicator, period, yAxisData);
                }
                
                // Render the custom chart
                renderCustomChart(data, indicatorData, chartType, yAxisData, indicator, period, selectedFile);
                
                // Perform custom analysis
                performCustomAnalysis(data, yAxisData, selectedFile);
            })
            .catch(error => {
                console.error('Error fetching data for custom chart:', error);
                document.getElementById('custom-chart').innerHTML = '<p class="text-danger">Error loading chart data</p>';
                document.getElementById('custom-analysis-results').innerHTML = '<p class="text-danger">Error performing analysis</p>';
            });
    }
    
    function calculateIndicator(data, indicator, period, dataField) {
        const prices = data.map(item => parseFloat(item[dataField]));
        
        switch (indicator) {
            case 'sma':
                return calculateSMA(prices, period);
            case 'ema':
                return calculateEMA(prices, period);
            case 'bollinger':
                return calculateBollingerBands(prices, period);
            default:
                return [];
        }
    }
    
    function calculateSMA(prices, period) {
        const sma = [];
        
        // Initialize with null values for the first (period-1) elements
        for (let i = 0; i < period - 1; i++) {
            sma.push(null);
        }
        
        // Calculate SMA for the rest
        for (let i = period - 1; i < prices.length; i++) {
            const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
            sma.push(sum / period);
        }
        
        return sma;
    }
    
    function calculateEMA(prices, period) {
        const ema = [];
        const multiplier = 2 / (period + 1);
        
        // Start with SMA for the first value
        let previousEMA = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;
        
        // Initialize with null values for the first (period-1) elements
        for (let i = 0; i < period - 1; i++) {
            ema.push(null);
        }
        
        // Add the first EMA
        ema.push(previousEMA);
        
        // Calculate EMA for the rest
        for (let i = period; i < prices.length; i++) {
            const currentEMA = (prices[i] - previousEMA) * multiplier + previousEMA;
            ema.push(currentEMA);
            previousEMA = currentEMA;
        }
        
        return ema;
    }
    
    function calculateBollingerBands(prices, period) {
        const bands = {
            upper: [],
            middle: [],
            lower: []
        };
        
        // Initialize with null values for the first (period-1) elements
        for (let i = 0; i < period - 1; i++) {
            bands.upper.push(null);
            bands.middle.push(null);
            bands.lower.push(null);
        }
        
        // Calculate bands for the rest
        for (let i = period - 1; i < prices.length; i++) {
            const slice = prices.slice(i - period + 1, i + 1);
            const avg = slice.reduce((a, b) => a + b, 0) / period;
            
            // Calculate standard deviation
            const sqDiffs = slice.map(value => {
                const diff = value - avg;
                return diff * diff;
            });
            const stdDev = Math.sqrt(sqDiffs.reduce((a, b) => a + b, 0) / period);
            
            bands.middle.push(avg);
            bands.upper.push(avg + (2 * stdDev));
            bands.lower.push(avg - (2 * stdDev));
        }
        
        return bands;
    }
    
    function renderCustomChart(data, indicatorData, chartType, yAxisData, indicator, period, filename) {
        // Extract coin and timeframe from filename
        const parts = filename.split('_');
        const coin = parts[0];
        const timeframe = parts[1] || '';
        
        // Prepare data based on chart type
        let seriesData = [];
        
        if (chartType === 'candlestick') {
            // Candlestick requires OHLC data
            seriesData = [{
                name: `${coin} Price`,
                type: 'candlestick',
                data: data.map(item => ({
                    x: new Date(item.date),
                    y: [
                        parseFloat(item.open),
                        parseFloat(item.high),
                        parseFloat(item.low),
                        parseFloat(item.close)
                    ]
                }))
            }];
            
        } else {
            // Line, bar, or area charts
            seriesData = [{
                name: `${coin} ${yAxisData.charAt(0).toUpperCase() + yAxisData.slice(1)}`,
                type: chartType,
                data: data.map(item => ({
                    x: new Date(item.date),
                    y: parseFloat(item[yAxisData])
                }))
            }];
        }
        
        // Add indicator series if applicable
        if (indicator !== 'none') {
            if (indicator === 'bollinger') {
                // Add three series for Bollinger Bands
                seriesData.push({
                    name: 'Middle Band (SMA)',
                    type: 'line',
                    data: data.map((item, i) => ({
                        x: new Date(item.date),
                        y: indicatorData.middle[i]
                    }))
                });
                
                seriesData.push({
                    name: 'Upper Band',
                    type: 'line',
                    data: data.map((item, i) => ({
                        x: new Date(item.date),
                        y: indicatorData.upper[i]
                    }))
                });
                
                seriesData.push({
                    name: 'Lower Band',
                    type: 'line',
                    data: data.map((item, i) => ({
                        x: new Date(item.date),
                        y: indicatorData.lower[i]
                    }))
                });
                
            } else {
                // Add single indicator series
                seriesData.push({
                    name: indicator === 'sma' ? `Simple Moving Average (${period})` : `Exponential Moving Average (${period})`,
                    type: 'line',
                    data: data.map((item, i) => ({
                        x: new Date(item.date),
                        y: indicatorData[i]
                    }))
                });
            }
        }
        
        // Configure chart options
        const options = {
            series: seriesData,
            chart: {
                height: 350,
                type: chartType === 'candlestick' ? 'candlestick' : 'line', // ApexCharts uses 'line' as the base for mixed charts
                toolbar: {
                    show: true
                }
            },
            title: {
                text: `Custom ${coin} Analysis (${timeframe})`,
                align: 'left'
            },
            xaxis: {
                type: 'datetime',
                labels: {
                    datetimeUTC: false
                }
            },
            yaxis: {
                tooltip: {
                    enabled: true
                },
                labels: {
                    formatter: function(value) {
                        return value.toFixed(2);
                    }
                }
            },
            tooltip: {
                enabled: true
            },
            colors: ['#008FFB', '#00E396', '#FEB019', '#FF4560', '#775DD0']
        };
        
        // Clear the container and create chart
        document.getElementById('custom-chart').innerHTML = '';
        const chart = new ApexCharts(document.getElementById('custom-chart'), options);
        chart.render();
    }
    
    function performCustomAnalysis(data, yAxisData, filename) {
        // Extract coin from filename
        const coin = filename.split('_')[0];
        
        // Calculate various statistics
        const values = data.map(item => parseFloat(item[yAxisData]));
        const firstValue = values[0];
        const lastValue = values[values.length - 1];
        const maxValue = Math.max(...values);
        const minValue = Math.min(...values);
        const avgValue = values.reduce((a, b) => a + b, 0) / values.length;
        
        // Calculate returns
        const returns = [];
        for (let i = 1; i < values.length; i++) {
            returns.push((values[i] / values[i - 1]) - 1);
        }
        
        const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
        const stdReturn = Math.sqrt(returns.map(r => Math.pow(r - avgReturn, 2)).reduce((a, b) => a + b, 0) / returns.length);
        
        // Calculate max drawdown
        let maxDrawdown = 0;
        let peak = values[0];
        
        for (let i = 1; i < values.length; i++) {
            if (values[i] > peak) {
                peak = values[i];
            } else {
                const drawdown = (peak - values[i]) / peak;
                if (drawdown > maxDrawdown) {
                    maxDrawdown = drawdown;
                }
            }
        }
        
        // Format for display
        const formatNum = (num, decimals = 2) => {
            if (isNaN(num)) return 'N/A';
            return parseFloat(num).toFixed(decimals);
        };
        
        const formatPercent = (num) => {
            if (isNaN(num)) return 'N/A';
            return `<span class="${num >= 0 ? 'positive' : 'negative'}">${formatNum(num * 100)}%</span>`;
        };
        
        // Prepare the analysis summary
        const html = `
            <div class="row">
                <div class="col-md-6">
                    <h5>Price Statistics</h5>
                    <table class="table table-sm">
                        <tr>
                            <td>Starting Value:</td>
                            <td>${formatNum(firstValue)}</td>
                        </tr>
                        <tr>
                            <td>Ending Value:</td>
                            <td>${formatNum(lastValue)}</td>
                        </tr>
                        <tr>
                            <td>Maximum Value:</td>
                            <td>${formatNum(maxValue)}</td>
                        </tr>
                        <tr>
                            <td>Minimum Value:</td>
                            <td>${formatNum(minValue)}</td>
                        </tr>
                        <tr>
                            <td>Average Value:</td>
                            <td>${formatNum(avgValue)}</td>
                        </tr>
                        <tr>
                            <td>Total Change:</td>
                            <td>${formatPercent((lastValue / firstValue) - 1)}</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Performance Metrics</h5>
                    <table class="table table-sm">
                        <tr>
                            <td>Average Return:</td>
                            <td>${formatPercent(avgReturn)}</td>
                        </tr>
                        <tr>
                            <td>Return Volatility:</td>
                            <td>${formatPercent(stdReturn)}</td>
                        </tr>
                        <tr>
                            <td>Maximum Drawdown:</td>
                            <td class="negative">${formatPercent(maxDrawdown)}</td>
                        </tr>
                        <tr>
                            <td>Risk/Reward Ratio:</td>
                            <td>${formatNum(Math.abs(avgReturn / stdReturn))}</td>
                        </tr>
                        <tr>
                            <td>Annualized Return:</td>
                            <td>${formatPercent(avgReturn * 365)}</td>
                        </tr>
                        <tr>
                            <td>Data Points:</td>
                            <td>${values.length}</td>
                        </tr>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('custom-analysis-results').innerHTML = html;
    }
});