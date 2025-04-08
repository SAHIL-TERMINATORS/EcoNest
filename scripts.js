document.addEventListener("DOMContentLoaded", function () {
    // Preview uploaded image
    let imageUpload = document.getElementById('imageUpload');
    if (imageUpload) {
        imageUpload.addEventListener('change', function (event) {
            let reader = new FileReader();
            reader.onload = function (e) {
                let preview = document.getElementById('imagePreview');
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(event.target.files[0]);
        });
    }

    // Fetch and update dashboard stats
    let statsSection = document.getElementById('stats');
    if (statsSection) {
        fetch('/dashboard_json')
            .then(response => response.json())
            .then(data => {
                document.getElementById('plasticCount').innerText = data.total_plastic;
                document.getElementById('nftCount').innerText = data.total_nfts;
                document.getElementById('fundsRaised').innerText = "$" + data.total_funds;
            })
            .catch(error => console.error("Error fetching dashboard data:", error));
    }
});
