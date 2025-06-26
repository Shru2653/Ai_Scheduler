// Module data structure containing all learning content
const moduleData = {
    fcfs: {
        title: "First-Come, First-Serve (FCFS)",
        description: "FCFS is the simplest CPU scheduling algorithm where processes are executed in the order they arrive.",
        keyPoints: [
            "Non-preemptive scheduling algorithm",
            "Processes are executed in the order they arrive",
            "Simple to implement but may lead to convoy effect",
            "Fair but not optimal for average waiting time"
        ],
        simulation: {
            processes: [
                { id: 'P1', arrivalTime: 0, burstTime: 4 },
                { id: 'P2', arrivalTime: 1, burstTime: 3 },
                { id: 'P3', arrivalTime: 2, burstTime: 5 }
            ],
            timeQuantum: null
        },
        quiz: [
            {
                question: "What is the main characteristic of FCFS scheduling?",
                options: [
                    "Processes are executed in the order they arrive",
                    "Processes with higher priority are executed first",
                    "Shortest processes are executed first"
                ],
                correct: 0
            },
            {
                question: "What is the main disadvantage of FCFS?",
                options: [
                    "High CPU utilization",
                    "Convoy effect",
                    "Complex implementation"
                ],
                correct: 1
            },
            {
                question: "Is FCFS preemptive?",
                options: ["Yes", "No"],
                correct: 1
            }
        ]
    },
    sjf: {
        title: "Shortest Job First (SJF)",
        description: "SJF selects the process with the smallest execution time to execute next.",
        keyPoints: [
            "Can be preemptive (SJF) or non-preemptive (SJN)",
            "Minimizes average waiting time",
            "Requires knowledge of process execution time",
            "May lead to starvation of long processes"
        ],
        simulation: {
            processes: [
                { id: 'P1', arrivalTime: 0, burstTime: 6 },
                { id: 'P2', arrivalTime: 1, burstTime: 4 },
                { id: 'P3', arrivalTime: 2, burstTime: 2 }
            ],
            timeQuantum: null
        },
        quiz: [
            {
                question: "What is the main advantage of SJF?",
                options: [
                    "High CPU utilization",
                    "Minimizes average waiting time",
                    "Simple implementation"
                ],
                correct: 1
            },
            {
                question: "What is the main challenge in implementing SJF?",
                options: [
                    "Process priority",
                    "Knowing burst times in advance",
                    "Time quantum selection"
                ],
                correct: 1
            }
        ]
    },
    rr: {
        title: "Round Robin (RR)",
        description: "Each process is assigned a fixed time slot (quantum) in a cyclic way.",
        keyPoints: [
            "Preemptive scheduling algorithm",
            "Each process gets a fixed time quantum",
            "Fair and starvation-free",
            "Good for time-sharing systems"
        ],
        simulation: {
            processes: [
                { id: 'P1', arrivalTime: 0, burstTime: 4 },
                { id: 'P2', arrivalTime: 1, burstTime: 3 },
                { id: 'P3', arrivalTime: 2, burstTime: 5 }
            ],
            timeQuantum: 2
        },
        quiz: [
            {
                question: "What is the key feature of Round Robin?",
                options: [
                    "Processes are executed in order of arrival",
                    "Each process gets a fixed time quantum",
                    "Processes with higher priority execute first"
                ],
                correct: 1
            },
            {
                question: "What happens when a process's time quantum expires?",
                options: [
                    "The process is terminated",
                    "The process is moved to the end of the ready queue",
                    "The process gets a new time quantum"
                ],
                correct: 1
            }
        ]
    },
    priority: {
        title: "Priority Scheduling",
        description: "Each process is assigned a priority and the process with the highest priority is executed first.",
        keyPoints: [
            "Can be preemptive or non-preemptive",
            "Processes are executed based on priority",
            "May lead to starvation of low-priority processes",
            "Used in real-time systems"
        ],
        simulation: {
            processes: [
                { id: 'P1', arrivalTime: 0, burstTime: 4, priority: 2 },
                { id: 'P2', arrivalTime: 1, burstTime: 3, priority: 1 },
                { id: 'P3', arrivalTime: 2, burstTime: 5, priority: 3 }
            ],
            timeQuantum: null
        },
        quiz: [
            {
                question: "What is the main issue with Priority Scheduling?",
                options: [
                    "High CPU utilization",
                    "Starvation of low-priority processes",
                    "Complex implementation"
                ],
                correct: 1
            },
            {
                question: "How can priority scheduling be made fairer?",
                options: [
                    "Increasing time quantum",
                    "Aging technique",
                    "Decreasing priorities"
                ],
                correct: 1
            }
        ]
    }
};

// Main Learning Module Class
class LearningModule {
    constructor() {
        this.currentModule = null;
        this.completedModules = new Set();
        this.quizScore = 0;
        this.simulationState = {
            isRunning: false,
            currentStep: 0,
            interval: null
        };

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Module selection
        document.querySelectorAll('.module-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const moduleId = e.target.closest('.module-btn').dataset.module;
                this.loadModule(moduleId);
            });
        });

        // Quiz answer selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.quiz-option')) {
                this.handleQuizAnswer(e.target.closest('.quiz-option'));
            }
        });

        // Simulation controls
        document.addEventListener('click', (e) => {
            if (e.target.matches('.simulation-control')) {
                const action = e.target.dataset.action;
                this.handleSimulationControl(action);
            }
        });
    }

    async loadModule(moduleId) {
        try {
            console.log('Loading module:', moduleId);
            
            // Show loading state
            this.showLoading();
            
            // Fade out current content
            const moduleContent = document.getElementById('module-content');
            if (moduleContent) {
                moduleContent.classList.add('fade-out');
                await new Promise(resolve => setTimeout(resolve, 300));
            }

            // Update active state
            document.querySelectorAll('.module-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            const activeBtn = document.querySelector(`[data-module="${moduleId}"]`);
            if (activeBtn) {
                activeBtn.classList.add('active');
            }

            // Get module data
            const module = moduleData[moduleId];
            if (!module) {
                throw new Error(`Module not found: ${moduleId}`);
            }

            // Create module content
            const content = this.createModuleContent(module);
            if (moduleContent) {
                moduleContent.innerHTML = content;
                
                // Initialize module-specific features
                await this.initializeModuleFeatures(moduleId);
                
                // Fade in new content
                moduleContent.classList.remove('fade-out');
                moduleContent.classList.add('fade-in');
            }

        } catch (error) {
            console.error('Error loading module:', error);
            this.showError(error.message);
        } finally {
            this.hideLoading();
        }
    }

    createModuleContent(module) {
        return `
            <div class="module-content">
                <h2 class="text-2xl font-bold text-gray-800 mb-4">${module.title}</h2>
                <div class="prose max-w-none">
                    <p class="text-gray-600 mb-4">${module.description}</p>
                    
                    <div class="key-characteristics p-4 rounded-lg mb-6">
                        <h3 class="text-lg font-semibold mb-2">Key Characteristics:</h3>
                        <ul class="list-disc list-inside text-gray-600 space-y-2">
                            ${module.keyPoints.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    </div>

                    <div class="simulation-section mb-6">
                        <h3 class="text-xl font-bold mb-4">Interactive Simulation</h3>
                        <div class="gantt-chart mb-4" id="gantt-chart"></div>
                        <div class="flex gap-4">
                            <button class="simulation-control px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition" data-action="start">
                                Start Simulation
                            </button>
                            <button class="simulation-control px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition" data-action="next" disabled>
                                Next Step
                            </button>
                            <button class="simulation-control px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition" data-action="reset" disabled>
                                Reset
                            </button>
                        </div>
                    </div>

                    <div class="quiz-section mt-8">
                        <h3 class="text-xl font-bold mb-4">Quick Quiz</h3>
                        <div class="space-y-4" id="quiz-container">
                            ${this.createQuizContent(module.quiz)}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createQuizContent(quiz) {
        return quiz.map((q, index) => `
            <div class="quiz-question" data-question="${index}">
                <p class="font-medium mb-2">${index + 1}. ${q.question}</p>
                <div class="space-y-2">
                    ${q.options.map((opt, optIndex) => `
                        <button class="w-full text-left px-4 py-3 rounded-lg quiz-option" 
                                data-correct="${optIndex === q.correct}">
                            ${opt}
                        </button>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    handleQuizAnswer(option) {
        if (option.classList.contains('answered')) return;
        
        const isCorrect = option.dataset.correct === 'true';
        option.classList.add('answered');
        
        if (isCorrect) {
            option.classList.add('correct');
            this.quizScore += 10;
        } else {
            option.classList.add('incorrect');
        }
        
        // Update score display
        document.querySelector('.quiz-score').textContent = this.quizScore;
        
        // Disable other options
        option.closest('.quiz-question').querySelectorAll('.quiz-option').forEach(opt => {
            if (opt !== option) opt.disabled = true;
        });
    }

    showLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('active');
        }
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.remove('active');
        }
    }

    showError(message) {
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        if (errorMessage && errorText) {
            errorText.textContent = message;
            errorMessage.classList.add('active');
            setTimeout(() => {
                errorMessage.classList.remove('active');
            }, 5000);
        }
    }
}

// Initialize learning module when the page loads
document.addEventListener('DOMContentLoaded', function() {
    try {
        window.learningModule = new LearningModule();
    } catch (error) {
        console.error('Failed to initialize learning module:', error);
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        if (errorMessage && errorText) {
            errorText.textContent = 'Failed to initialize learning module. Please refresh the page.';
            errorMessage.classList.add('active');
        }
    }
}); 