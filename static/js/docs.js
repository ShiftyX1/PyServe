document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-links a');
    
    const pageCache = {};
    
    navLinks.forEach(link => {
        link.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const pageId = this.getAttribute('data-page');
            
            navLinks.forEach(l => l.classList.remove('active'));
            
            this.classList.add('active');
            
            document.querySelectorAll('.page').forEach(page => {
                page.classList.remove('active');
            });
            
            const existingPage = document.getElementById(pageId);
            
            if (existingPage) {
                existingPage.classList.add('active');
            } else {
                await loadPage(pageId);
            }
            
            window.scrollTo(0, 0);
        });
    });
    
    document.addEventListener('click', function(e) {
        if (e.target.matches('.button[data-page]') || e.target.closest('.button[data-page]')) {
            const button = e.target.matches('.button[data-page]') ? e.target : e.target.closest('.button[data-page]');
            const pageId = button.getAttribute('data-page');
            
            const navLink = document.querySelector(`.nav-links a[data-page="${pageId}"]`);
            if (navLink) {
                navLink.click();
            }
            
            e.preventDefault();
        }
    });
    
    async function loadPage(pageId) {
        try {
            let pageContent;
            
            if (pageCache[pageId]) {
                pageContent = pageCache[pageId];
            } else {
                const response = await fetch(`/static/pages/${pageId}.html`);
                
                if (!response.ok) {
                    throw new Error(`Failed to load page: ${response.status}`);
                }
                
                pageContent = await response.text();
                
                pageCache[pageId] = pageContent;
            }
            
            const pageElement = document.createElement('div');
            pageElement.className = 'page active';
            pageElement.id = pageId;
            pageElement.innerHTML = pageContent;
            
            document.querySelector('.content').appendChild(pageElement);
            
            if (typeof Prism !== 'undefined') {
                Prism.highlightAllUnder(pageElement);
            }
            
        } catch (error) {
            console.error('Error loading page:', error);
            
            const errorPage = document.createElement('div');
            errorPage.className = 'page active';
            errorPage.id = pageId;
            errorPage.innerHTML = `
                <div class="header-banner">
                    <h1>Error</h1>
                </div>
                <div class="card">
                    <h2>Failed to Load Content</h2>
                    <div class="alert alert-error">
                        <p>Sorry, we couldn't load the requested page. Please try again later.</p>
                        <p>Error: ${error.message}</p>
                    </div>
                </div>
            `;
            
            document.querySelector('.content').appendChild(errorPage);
        }
    }
    
    document.addEventListener('click', function(e) {
        if (e.target.matches('.copy-code') || e.target.closest('.copy-code')) {
            const button = e.target.matches('.copy-code') ? e.target : e.target.closest('.copy-code');
            const codeBlock = button.parentElement.querySelector('code');
            
            if (codeBlock) {
                const textToCopy = codeBlock.textContent;
                
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const originalText = button.textContent;
                    button.textContent = 'Copied!';
                    button.classList.add('copied');
                    
                    setTimeout(() => {
                        button.textContent = originalText;
                        button.classList.remove('copied');
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy code:', err);
                });
            }
        }
    });
    
    function addCopyButtons() {
        document.querySelectorAll('.code-block').forEach(block => {
            if (!block.querySelector('.copy-code')) {
                const copyButton = document.createElement('button');
                copyButton.className = 'copy-code';
                copyButton.textContent = 'Copy';
                block.appendChild(copyButton);
            }
        });
    }
    
    addCopyButtons();
    
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.addedNodes.length) {
                addCopyButtons();
            }
        });
    });
    
    observer.observe(document.querySelector('.content'), { childList: true, subtree: true });
});

document.addEventListener('click', function(e) {
    if (e.target.matches('.run-example') || e.target.closest('.run-example')) {
        const button = e.target.matches('.run-example') ? e.target : e.target.closest('.run-example');
        const codeBlock = button.closest('.example-container').querySelector('code');
        const outputBlock = button.closest('.example-container').querySelector('.example-output');
        
        if (codeBlock && outputBlock) {
            try {
                const code = codeBlock.textContent;
                outputBlock.innerHTML = '<div class="example-result">Code execution simulated. In a real environment, this would execute the Python code.</div>';
                outputBlock.style.display = 'block';
            } catch (error) {
                outputBlock.innerHTML = `<div class="example-error">Error: ${error.message}</div>`;
                outputBlock.style.display = 'block';
            }
        }
    }
});