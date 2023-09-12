<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $name = $_POST["Name"];
    $email = $_POST["Email"];
    $message = $_POST["Message"];
    
    $to = "darmstater12@gmail.com"; // Ganti dengan alamat email Anda
    $subject = "Pesan dari $name";
    $headers = "From: $email";

    if (mail($to, $subject, $message, $headers)) {
        echo "Pesan berhasil dikirim.";
    } else {
        echo "Pesan gagal dikirim. Silakan coba lagi.";
    }
}
?>
