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
            const month_day = this.currentDate.getDay();
            
            const firstDay = new Date(year, month, 1).getDay();
            const lastDay = new Date(year, month + 1, 0).getDate();
            
            this.days = [];
            
            for (let i = 0; i < firstDay; i++) {
                this.days.push({ date: '', current: false });
            }
            
            for (let day = 1; day <= lastDay; day++) {
                this.days.push({ date: day, current: true, })
            }
            
            while (this.days.length % 7 !== 0) {
                this.days.push({ date: '', current: false });
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