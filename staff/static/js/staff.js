class Staff{
    // #memberBtn = document.querySelectorAll('.member-item');
    #panel = document.querySelector('.panel');
    #side = document.querySelector('.side');
    #isActive = false;
    #toolbarChips = document.querySelector('.toolbar .chips');
    constructor(){
        this.#panel.addEventListener('click', (e)=>{
            let memberItem = e.target.closest('.member-item');
            if(memberItem){
                if(memberItem.classList.contains('active')){
                    memberItem.classList.remove('active');
                    this.#isActive = false;
                    this.#side.innerHTML = '';
                    return;
                }
                document.querySelectorAll('.member-item').forEach(item => item.classList.remove('active'));
                memberItem.classList.add('active');
                this.#isActive = true;
                console.log(memberItem.dataset.memberid);
                this._showMemberDetails(memberItem.dataset.memberid);
            }
        });

        this.#toolbarChips.addEventListener('click', (e)=>{
            let chip = e.target.closest('.chip');
            if(chip){
                document.querySelectorAll('.chip').forEach(item => item.classList.remove('active'));
                chip.classList.add('active');
                let chipValue = chip.textContent.trim();
                window.location.href = `/staff/?filter=${encodeURIComponent(chipValue)}`;
            }
        });
    }

    async _showMemberDetails(memberId){
        const url = `/staff/api/staff-details/${memberId}/`;
        const response = await fetch(url);
        if(!response.ok){
            console.error('Failed to fetch staff details');
            return;
        }
        const data = await response.json();
        this._displayMemberDetails(data);
    }

    _displayMemberDetails(data){

        console.log(data);

        let html = `
        <div>
        <p class="member-name" style="margin-bottom: 0.15rem;">${data.first_name} ${data.last_name}</p>
        <p class="member-role">Sales lead · ${data.department}</p>
        <p class="member-role">Offline · last seen active now · ${data.active_company}</p>
      </div>

      <div class="contact">
        <a href="mailto:${data.email}">${data.email}</a>
        <a href="tel:${data.phone_number}">${data.phone_number}</a>
      </div>

      <div class="history">
        <div class="history-head">
          <span class="history-title">Conversation history</span>
          <input class="search" style="padding: 0.35rem 0.55rem; min-width: 220px;" placeholder="Search e.g. quote Q-7781" />
        </div>
        <div class="history-list">
          <article class="msg">
            <div class="msg-head"><span>Chat · You</span><span>26 cze, 04:47</span></div>
            <p>Sure, I will send a revised pricing sheet today.</p>
          </article>
          <article class="msg">
            <div class="msg-head"><span>Chat · Anna</span><span>26 cze, 03:47</span></div>
            <p>Hi! Let me know if you need pricing on the latest quote.</p>
          </article>
          <article class="msg">
            <div class="msg-head"><span>Email · Sent</span><span>25 cze, 06:47</span></div>
            <p><strong>Re: Quote Q-7781 follow-up</strong></p>
            <p>Confirmed on our side, please proceed.</p>
          </article>
          <article class="msg">
            <div class="msg-head"><span>Email · Received</span><span>25 cze, 04:47</span></div>
            <p><strong>Quote Q-7781 follow-up</strong></p>
            <p>Hi, do we have approval on Q-7781? The customer is waiting on confirmation.</p>
          </article>
        </div>
      </div>

      <div class="composer">
        <h5>Chat</h5>
        <form>
          <input placeholder="Message Anna" />
          <button class="btn btn-primary" type="submit" disabled>Send</button>
        </form>
      </div>

      <div class="composer">
        <h5>Email</h5>
        <form>
          <input placeholder="Subject" />
          <textarea rows="3" placeholder="Write to Anna Kowalska..."></textarea>
          <button class="btn btn-primary" type="submit" disabled>Send email</button>
        </form>
      </div>
        `

        this.#side.innerHTML = html;
    }
}


const staff = new Staff();