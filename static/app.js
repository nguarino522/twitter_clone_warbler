document.addEventListener("DOMContentLoaded", (event) => {

    const likeBtns = Array.from(document.getElementsByClassName("fa-thumbs-up"));
    
    likeBtns.forEach(likeBtn => {
        likeBtn.addEventListener("click", function (e) {
            e.preventDefault();
            console.log(e)
            let likeBtnParentElement = likeBtn.parentElement
            let msgId = likeBtn.getAttribute("data-id");
            toggleLikeButton(msgId, likeBtnParentElement);
        });
    });

    async function toggleLikeButton(msgId, likeBtnParentElement) {
        let resp = await axios.post(`/users/toggle_like/${msgId}`)
        console.log(resp.data.msg_liked);
        if (resp.data.msg_liked === true) {
            likeBtnParentElement.classList.remove("btn-secondary");
            likeBtnParentElement.classList.add("btn-primary");
        } else {
            likeBtnParentElement.classList.remove("btn-primary");
            likeBtnParentElement.classList.add("btn-secondary");
        }
    }
});

