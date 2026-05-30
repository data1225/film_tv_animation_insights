// Define global variables
window.timeData = {
  lastYear: new Date().getFullYear() - 1,
  twoYearsAgo: new Date().getFullYear() - 2,
  threeYearsAgo: new Date().getFullYear() - 3,
  todayDate: new Date().toISOString().split('T')[0],
};

document.addEventListener('DOMContentLoaded', () => {
  
  // --- Inject year & date --- //
  // Inject year into text spans
  document.querySelectorAll('[data-year-text]').forEach(el => {
    const key = el.getAttribute('data-year-text');
    if (window.timeData[key] !== undefined) {
      el.textContent = window.timeData[key];
    }
  });

  // Replace {year} in anchor hrefs
  document.querySelectorAll('[data-year-href]').forEach(el => {
    const key = el.getAttribute('data-year-href');
    const href = el.getAttribute('href');
    if (window.timeData[key] !== undefined && href.includes('{year}')) {
      el.setAttribute('href', href.replace(/{year}/g, window.timeData[key]));
    }
  });

  // Replace {date} in anchor hrefs
  document.querySelectorAll('[data-date-href]').forEach(el => {
    const key = el.getAttribute('data-date-href');
    const href = el.getAttribute('href');
    if (window.timeData[key] !== undefined && href.includes('{date}')) {
      el.setAttribute('href', href.replace(/{date}/g, window.timeData[key]));
    }
  });    
  // --- Inject year & date End --- //


  // --- 統一處理平滑滾動與網址錨點更新 --- //
  
  // 共用滾動與更新網址的函式
  const handleAnchorScroll = (e, link) => {
    const href = link.getAttribute('href');
    
    // 確保是內部錨點連結 (以 # 開頭)
    if (href && href.startsWith('#')) {
      const id = href.substring(1);
      const target = document.getElementById(id);
      
      if (target) {
        e.preventDefault(); // 阻止瀏覽器預設瞬間跳轉
        
        // 1. 平滑滾動到目標元素
        target.scrollIntoView({ behavior: 'smooth' });
        
        // 2. 更新瀏覽器網址列的 Hash，且不觸發頁面跳動
        history.pushState(null, null, href);
      }
    }
  };

  // 為 TOC (目錄) 綁定事件
  document.querySelectorAll('#toc a').forEach(link => {
    link.addEventListener('click', (e) => handleAnchorScroll(e, link));
  });

  // 為其他導覽選單 (Menu) 綁定事件
  document.querySelectorAll('.menu a').forEach(link => {
    link.addEventListener('click', (e) => handleAnchorScroll(e, link));
  });


  // --- 處理載入網頁時，網址自帶錨點的自動平滑滾動 --- //
  const handleInitialHashRedirect = () => {
    const hash = window.location.hash;
    if (hash) {
      const id = hash.substring(1);
      const target = document.getElementById(id);
      
      if (target) {
        // 先將網頁滾動稍微重置或防止瀏覽器預設跳轉造成的突兀
        // 使用 setTimeout 微幅延遲，確保 DOM 排版與圖片載入完成，滾動位置才會精確
        setTimeout(() => {
          target.scrollIntoView({ behavior: 'smooth' });
        }, 150); 
      }
    }
  };

  // 執行初始錨點檢查
  handleInitialHashRedirect();
});

// Other custom functions
function scrollToToc() {
  const toc = document.getElementById("toc");
  if (toc) {
    toc.scrollIntoView({ behavior: "smooth" });
    // 同步更新網址為 #toc
    history.pushState(null, null, '#toc');
  } else {
    window.scrollTo({ top: 0, behavior: "smooth" });
    // 回到頂部時清除 hash
    history.pushState(null, null, window.location.pathname);
  }
}