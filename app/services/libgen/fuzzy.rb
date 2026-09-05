module Libgen
  # Port of fuzzywuzzy's token_sort_ratio from the desktop Books app:
  # process each string (drop characters 128-255, replace remaining
  # non-word characters with whitespace, lowercase, trim), sort the
  # whitespace-separated tokens, and score the sorted strings with
  # difflib's Ratcliff-Obershelp ratio.
  module Fuzzy
    module_function

    def token_sort_ratio(first, second)
      return 0 if first.nil? || second.nil?
      return 100 if first == second

      ratio(sort_tokens(first), sort_tokens(second))
    end

    def sort_tokens(value)
      value = value.gsub(/[\u0080-\u00FF]/, "")
      value = value.gsub(/[^\p{Word}]/u, " ")
      value = value.downcase.strip
      value.split.sort.join(" ")
    end

    def ratio(first, second)
      return 0 if first.nil? || second.nil?
      return 100 if first == second
      return 0 if first.empty? || second.empty?

      round_half_even(200 * matched(first, second), first.length + second.length)
    end

    def matched(a, b, alo = 0, ahi = a.length, blo = 0, bhi = b.length)
      i, j, k = longest_match(a, b, alo, ahi, blo, bhi)
      return 0 if k.zero?

      k + matched(a, b, alo, i, blo, j) + matched(a, b, i + k, ahi, j + k, bhi)
    end

    # The longest common substring of a[alo...ahi) and b[blo...bhi), returned
    # as [a_start, b_start, length] with difflib's tie-breaking (the earliest
    # maximal block wins).
    def longest_match(a, b, alo, ahi, blo, bhi)
      best_i = alo
      best_j = blo
      best_k = 0
      previous = Array.new(bhi - blo + 1, 0)
      (alo...ahi).each do |i|
        current = [ 0 ]
        (blo...bhi).each_with_index do |j, index|
          length = b[j] == a[i] ? previous[index] + 1 : 0
          current << length
          next unless length > best_k

          best_k = length
          best_i = i - length + 1
          best_j = blo + index - length + 1
        end
        previous = current
      end
      [ best_i, best_j, best_k ]
    end

    # Python's int(round(x)) rounds halves to the even neighbour.
    def round_half_even(numerator, denominator)
      quotient, remainder = numerator.divmod(denominator)
      if remainder * 2 == denominator
        quotient.even? ? quotient : quotient + 1
      elsif remainder * 2 > denominator
        quotient + 1
      else
        quotient
      end
    end
  end
end
