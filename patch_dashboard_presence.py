import re
with open('frontend/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

presence_code = '''
                        const myState = {
                            user_id: user_id,
                            role: 'patient',
                            full_name: 'Patient',
                            last_seen: new Date().toISOString()
                        };
                        this.presenceChannel = sb.channel('adhera-presence');
                        this.presenceChannel.subscribe(async (status) => {
                            if (status === 'SUBSCRIBED') {
                                await this.presenceChannel.track(myState);
                                setInterval(async () => {
                                    myState.last_seen = new Date().toISOString();
                                    await this.presenceChannel.track(myState);
                                }, 30000);
                            }
                        });
                        window.addEventListener('beforeunload', () => {
                            this.presenceChannel.untrack();
                        });
'''

content = content.replace('.subscribe();', '.subscribe();' + presence_code)
content = content.replace("sessionStorage.removeItem('jwt');", "if(this.presenceChannel) this.presenceChannel.untrack(); sessionStorage.removeItem('jwt');")
content = content.replace('charts: {},', 'charts: {}, presenceChannel: null,')

with open('frontend/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
