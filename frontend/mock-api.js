// Mock API for frontend testing when backend is not available
class MockAPI {
    constructor() {
        this.baseURL = 'https://woke-one.vercel.app/api';
        this.mockData = {
            users: [],
            tasks: [],
            bookings: [],
            taskers: [
                { id: '1', name: 'John Smith', skills: ['Cleaning', 'Repairs'], hourly_rate: 25, bio: 'Professional cleaner with 5 years experience' },
                { id: '2', name: 'Sarah Johnson', skills: ['Beauty', 'Wellness'], hourly_rate: 35, bio: 'Certified beauty therapist' },
                { id: '3', name: 'Mike Wilson', skills: ['Car Care', 'Repairs'], hourly_rate: 30, bio: 'Auto repair specialist' }
            ]
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (response.ok) {
                return await response.json();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.warn(`API call failed, using mock data: ${error.message}`);
            return this.getMockResponse(endpoint, options);
        }
    }

    getMockResponse(endpoint, options) {
        const method = options.method || 'GET';
        
        switch (endpoint) {
            case '/':
                return { message: "Backend running", status: "success" };
                
            case '/register/customer':
                const registerData = JSON.parse(options.body || '{}');
                const newUser = {
                    id: Date.now().toString(),
                    name: registerData.name,
                    email: registerData.email,
                    role: 'customer'
                };
                this.mockData.users.push(newUser);
                return {
                    message: "Customer registered successfully",
                    user_id: newUser.id,
                    email: newUser.email
                };
                
            case '/login/customer':
                const loginData = JSON.parse(options.body || '{}');
                const user = this.mockData.users.find(u => u.email === loginData.email);
                if (user) {
                    return {
                        message: "Login successful",
                        user_id: user.id,
                        email: user.email,
                        name: user.name,
                        user_name: user.name, // Also include user_name for compatibility
                        role: user.role
                    };
                } else {
                    throw new Error("Invalid credentials");
                }
                
            case '/tasks':
                if (method === 'POST') {
                    const taskData = JSON.parse(options.body || '{}');
                    const newTask = {
                        id: Date.now(),
                        ...taskData,
                        created_at: new Date().toISOString()
                    };
                    this.mockData.tasks.push(newTask);
                    return { message: "Task created", task: newTask };
                }
                return { tasks: this.mockData.tasks };
                
            case '/taskers':
                return { taskers: this.mockData.taskers };
                
            case '/bookings':
                if (method === 'POST') {
                    const bookingData = JSON.parse(options.body || '{}');
                    const newBooking = {
                        id: Date.now(),
                        ...bookingData,
                        status: 'pending',
                        created_at: new Date().toISOString()
                    };
                    this.mockData.bookings.push(newBooking);
                    return { message: "Booking created", booking: newBooking };
                }
                const customerId = new URLSearchParams(window.location.search).get('customer_id');
                const userBookings = this.mockData.bookings.filter(b => b.customer_id === customerId);
                return { bookings: userBookings };
                
            default:
                return { message: "Endpoint not found", status: "error" };
        }
    }
}

// Create global API instance
window.api = new MockAPI();

// Override fetch for API calls
const originalFetch = window.fetch;
window.fetch = async (url, options = {}) => {
    if (url.includes('/api/')) {
        const endpoint = url.replace('https://woke-one.vercel.app', '');
        return {
            ok: true,
            json: async () => await window.api.request(endpoint, options)
        };
    }
    return originalFetch(url, options);
};
