##### spearman correlation code

# install.packages("R.matlab")
library(R.matlab)

folder <- "/Users/in65/Desktop/FinalResults/FCNirs_mat"

files <- list(
  Dis  = file.path(folder, "Dis_Group_conc_corrRMap.mat"),
  Eng  = file.path(folder, "Eng_Group_conc_corrRMap.mat"),
  Rest = file.path(folder, "Rest_Group_conc_corrRMap.mat"),
  Span = file.path(folder, "Span_Group_conc_corrRMap.mat")
)

# --- Extract HbO (first element) ---
get_HbO <- function(f) {
  data <- readMat(f)
  mat <- data$concMap[[1]]   # HbO
  mat <- as.matrix(mat)
  storage.mode(mat) <- "numeric"
  return(mat)
}

mat_list <- lapply(files, get_HbO)

# --- Upper triangle ---
get_upper_tri <- function(mat) {
  as.numeric(mat[upper.tri(mat, diag = FALSE)])
}

vec_list <- lapply(mat_list, get_upper_tri)

# Sanity check
print(sapply(vec_list, length))

n <- length(vec_list)

# --- Initialize result matrices ---
cor_mat <- matrix(NA, n, n,
                  dimnames = list(names(vec_list), names(vec_list)))
p_mat   <- matrix(NA, n, n,
                  dimnames = list(names(vec_list), names(vec_list)))

# --- Compute correlations + p-values ---
for (i in 1:n) {
  for (j in 1:n) {
    test <- cor.test(vec_list[[i]], vec_list[[j]],
                     method = "spearman",
                     exact = FALSE,
                     use = "complete.obs")
    
    cor_mat[i, j] <- unname(test$estimate)
    p_mat[i, j]   <- test$p.value
  }
}

# Output
cat("Spearman correlation matrix (rho):\n")
print(cor_mat)

cat("\nP-value matrix:\n")
print(p_mat)

# Optional: FDR correction
p_mat_fdr <- matrix(p.adjust(p_mat, method = "fdr"), n, n)
dimnames(p_mat_fdr) <- dimnames(p_mat)

cat("\nFDR-corrected p-values:\n")
print(p_mat_fdr)
