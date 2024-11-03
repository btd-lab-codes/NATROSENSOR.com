function clock() {
    return {
        date: "",
        time: "",
        init() {
            this.getDatetime();
            setInterval(()=> this.getDatetime(), 1000)
        },
        getDatetime() {
            const now = new Date();
            this.date = now.toLocaleString('default', { year: 'numeric', month: 'long', day: 'numeric' });
            this.time = now.toLocaleTimeString();
        }
    };
}

function calendar() {
    return {
        currentDate: new Date(),
        days: [],
        init() {
            this.updateCalendar();
            this.updateMonthYear();
        },
        updateCalendar() {
            const year = this.currentDate.getFullYear();
            const month = this.currentDate.getMonth();

            const today_year = new Date().getFullYear();
            const today_month = new Date().getMonth();
            const today_day = new Date().getDate();
            
            const firstDay = new Date(year, month, 1).getDay();
            const lastDay = new Date(year, month + 1, 0).getDate();

            const options = { year: 'numeric', month: 'long', day: 'numeric' };           
            this.days = [];
            
            for (let i = 0; i < firstDay; i++) {
                this.days.push({ date: '', stringDate: '', current: false, today: false });
            }
            
            for (let day = 1; day <= lastDay; day++) {
                let today = (today_year == year && today_month == month && today_day == day ) ? true : false;
                let formatDate = new Date(year, month, day).toLocaleDateString(undefined, options);
                this.days.push({ date: day, stringDate: formatDate, current: true, today: today });
            }
            
            while (this.days.length != 42) {
                this.days.push({ date: '', stringDate: '', current: false, today: false });
            }
        },
        prevMonth() {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.updateCalendar();
            this.updateMonthYear();
        },
        nextMonth() {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.updateCalendar();
            this.updateMonthYear();
        },
        updateMonthYear() {
            const options = { month: 'long', year: 'numeric' };
            this.$refs.monthYear.textContent = this.currentDate.toLocaleDateString(undefined, options);
        }
    }
}

function eventFilter(selectedDate, events) {
    return {
        selectedDate: selectedDate,
        events: events,
        filteredEvents: [],
        filterEvents() {
            this.filteredEvents = this.events.map(event => {
                return event.getDate() === this.selectedDate;
            });
        }
    };
}