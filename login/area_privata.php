<?php

require_once('config.php');
$_SESSION['connessioneAttiva'] = true;

// Se non abbiamo una sessione attiva, reindirizza l'utente al login per accedere all'area privata
if (!isset($_SESSION['user_name'])) {
   header('location:../index');
   exit; // Aggiunto per terminare l'esecuzione dello script dopo il reindirizzamento
}
?>

<!DOCTYPE html>
<html lang="en">

<head>
   <meta charset="UTF-8">
   <meta http-equiv="X-UA-Compatible" content="IE=edge">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>Area Privata</title>
   <link rel="stylesheet" href="../css/style.css">
   <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.4/jquery.min.js"></script>
</head>

<body>

   <div class="container">

      <div class="content">
         <h1>Ciao <span><?php echo $_SESSION['user_name']; ?></span></h1>
         <p>Questa è la tua Area Privata</p>
         <a href="../" class="btn">Login</a>
         <a href="logout" class="btn">Logout</a>
      </div>

   </div>

</body>

</html>