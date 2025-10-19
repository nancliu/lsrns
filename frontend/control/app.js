// 导航切换逻辑
document.addEventListener('DOMContentLoaded', () => {
    const navButtons = document.querySelectorAll('.nav-btn');
    const viewSections = document.querySelectorAll('.view-content');

    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const viewName = button.getAttribute('data-view');

            // 更新按钮激活状态
            navButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            // 更新视图显示
            viewSections.forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(`view-${viewName}`).classList.add('active');

            // 保存当前视图到 sessionStorage (页面刷新保持状态)
            sessionStorage.setItem('activeView', viewName);
        });
    });

    // 页面加载时恢复上次激活的视图
    const savedView = sessionStorage.getItem('activeView');
    if (savedView) {
        const savedButton = document.querySelector(`[data-view="${savedView}"]`);
        if (savedButton) {
            savedButton.click();
        }
    }
});
