# AI-Powered Process Scheduler

An intelligent process scheduling system that implements various scheduling algorithms with real-time system monitoring and visualization.

## Features

- **Multiple Scheduling Algorithms**
  - Round Robin Scheduling
  - Priority Scheduling
  - AI-based Scheduling

- **Real-time System Monitoring**
  - CPU Utilization Tracking
  - Memory Usage Analysis
  - I/O Operations Monitoring

- **Interactive Dashboard**
  - Process Queue Visualization
  - Resource Allocation Charts
  - Performance Metrics Display

- **Visualization Tools**
  - Gantt Chart
  - Resource Usage Graphs
  - Performance Comparison Charts

## Technical Stack

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Visualization**: Chart.js
- **System Monitoring**: psutil
- **Database**: SQLite

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shru2653/Ai_Scheduler.git
   cd Ai_Scheduler
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Usage

1. Access the dashboard at `http://localhost:8000`
2. Navigate to the scheduling page
3. Select a scheduling algorithm
4. Configure process parameters
5. View real-time scheduling and system metrics

## Project Structure

```
Ai_Scheduler/
├── taskmanager/          # Main application
│   ├── migrations/       # Database migrations
│   ├── templates/        # HTML templates
│   ├── static/          # Static files
│   ├── models.py        # Database models
│   ├── views.py         # View functions
│   └── urls.py          # URL routing
├── scheduler/           # Scheduling algorithms
│   ├── round_robin.py   # Round Robin implementation
│   ├── priority.py      # Priority scheduling
│   └── ai_scheduler.py  # AI-based scheduling
└── manage.py           # Django management script
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Django Framework
- Chart.js for visualization
- psutil for system monitoring
