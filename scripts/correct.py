r"""
Romanian Translation Correction Script - Combined Pattern & LLM

Corrects existing Romanian translations in Ren'Py .rpy files using:
1. Pattern-based corrections (fast, reliable, from JSON file)
2. LLM-based corrections (slow, intelligent, using Aya-23-8B)

Usage:
    python correct.py <input_file_or_dir> [options]

Options:
    --patterns-only     Use only pattern-based corrections (fast)
    --llm-only          Use only LLM corrections (slow)
    --dry-run           Preview changes without writing files
    (default)           Use both: patterns first, then LLM

Examples:
    # Fast pattern-based corrections only
    python correct.py "game\tl\romanian" --patterns-only

    # Intelligent LLM corrections only
    python correct.py "game\tl\romanian" --llm-only

    # Combined approach (patterns first, then LLM)
    python correct.py "game\tl\romanian"

    # Preview without writing
    python correct.py "game\tl\romanian" --dry-run
"""

import re
import sys
import os
import json
import io
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import time



# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Fix Windows PATH for CUDA DLLs
if sys.platform == "win32":
    torch_lib = str(Path(__file__).parent.parent / "venv" / "Lib" / "site-packages" / "torch" / "lib")
    if os.path.exists(torch_lib) and torch_lib not in os.environ["PATH"]:
        os.environ["PATH"] = torch_lib + os.pathsep + os.environ["PATH"]

def show_progress(current, total, start_time, prefix=""):
    """Display simple progress bar with >>> characters and time labels"""
    percentage = (current / total) * 100 if total > 0 else 0
    elapsed = time.time() - start_time

    # Calculate ETA
    if current > 0 and elapsed > 0:
        rate = current / elapsed
        remaining = (total - current) / rate if rate > 0 else 0
    else:
        remaining = 0

    # Format time strings
    elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s" if elapsed >= 60 else f"{int(elapsed)}s"
    remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s" if remaining >= 60 else f"{int(remaining)}s"

    # Create progress bar with >>> characters
    bar_width = 50
    filled = int(bar_width * current / total) if total > 0 else 0
    bar = ">" * filled + " " * (bar_width - filled)

    # Display with labels
    print(f"\r{prefix}[{bar}] {current}/{total} ({percentage:.0f}%) | Elapsed: {elapsed_str} | ETA: {remaining_str}",
          end='', flush=True)


class PatternBasedCorrector:
    """Fast, reliable corrections using predefined patterns"""

    def __init__(self, corrections_file: str):
        """Load correction patterns from JSON file"""
        with open(corrections_file, 'r', encoding='utf-8') as f:
            self.corrections = json.load(f)

        self.protected_words = set(self.corrections.get('protected_words', []))
        print(f"[OK] Loaded pattern-based corrections")
        if self.protected_words:
            print(f"  Protected words: {', '.join(self.protected_words)}")

    def correct_text(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Apply pattern-based corrections to text

        Returns:
            (corrected_text, list_of_changes_made)
        """
        corrected = text
        changes = []

        # Apply exact replacements first
        for wrong, right in self.corrections.get('exact_replacements', {}).items():
            if wrong in corrected:
                # Need to replace selectively (only unprotected occurrences)
                new_text = []
                last_end = 0
                replaced = False

                for i in range(len(corrected) - len(wrong) + 1):
                    if corrected[i:i+len(wrong)] == wrong:
                        # Found occurrence - check if protected
                        if not self._is_occurrence_protected(i, wrong, corrected):
                            # Add text before this occurrence
                            new_text.append(corrected[last_end:i])
                            # Add replacement
                            new_text.append(right)
                            last_end = i + len(wrong)
                            replaced = True

                if replaced:
                    # Add remaining text
                    new_text.append(corrected[last_end:])
                    corrected = ''.join(new_text)
                    changes.append({
                        'type': 'exact',
                        'old': wrong,
                        'new': right
                    })

        # Apply verb conjugation patterns
        for pattern_def in self.corrections.get('verb_conjugations', []):
            pattern = pattern_def['pattern']
            replacement = pattern_def['replacement']

            regex = re.compile(pattern)
            matches = list(regex.finditer(corrected))

            for match in reversed(matches):
                old_text = match.group(0)
                if not any(word in old_text for word in self.protected_words):
                    corrected = corrected[:match.start()] + replacement + corrected[match.end():]
                    changes.append({
                        'type': 'verb_conjugation',
                        'old': old_text,
                        'new': replacement
                    })

        # Apply pronoun correction patterns
        for pattern_def in self.corrections.get('pronoun_corrections', []):
            pattern = pattern_def['pattern']
            replacement = pattern_def['replacement']

            regex = re.compile(pattern)
            matches = list(regex.finditer(corrected))

            for match in reversed(matches):
                old_text = match.group(0)
                corrected = corrected[:match.start()] + replacement + corrected[match.end():]
                changes.append({
                    'type': 'pronoun_correction',
                    'old': old_text,
                    'new': replacement
                })

        # Apply gender agreement patterns
        for pattern_def in self.corrections.get('gender_agreement', []):
            pattern = pattern_def['pattern']
            replacement = pattern_def['replacement']

            regex = re.compile(pattern)
            matches = list(regex.finditer(corrected))

            for match in reversed(matches):
                old_text = match.group(0)
                corrected = corrected[:match.start()] + replacement + corrected[match.end():]
                changes.append({
                    'type': 'gender_agreement',
                    'old': old_text,
                    'new': replacement
                })

        return corrected, changes

    def _is_occurrence_protected(self, position: int, text: str, context: str) -> bool:
        """Check if a specific occurrence of text at position is adjacent to a protected word"""
        # Get surrounding text (a few characters before and after)
        start = max(0, position - 20)
        end = min(len(context), position + len(text) + 20)
        surrounding = context[start:end]

        for protected in self.protected_words:
            if protected in surrounding:
                # Find position of protected word in surrounding text
                protected_pos_in_surrounding = surrounding.find(protected)
                text_pos_in_surrounding = position - start

                # Check if they're adjacent (within a few characters)
                distance = abs(protected_pos_in_surrounding - text_pos_in_surrounding)
                # Adjacent means the protected word and the text are touching or very close
                # e.g., "Ceau !" - "Ceau" and " !" are adjacent
                if distance <= len(protected) + 2:
                    return True
        return False


class LLMBasedCorrector:
    """Intelligent, context-aware corrections using Aya-23-8B"""

    TAG_PATTERN = re.compile(r'\{[^}]+\}')
    VAR_PATTERN = re.compile(r'\[[^\]]+\]')

    def __init__(self, model_path: str):
        """Initialize LLM corrector with Aya-23-8B model"""
        from core import Aya23Translator
        print("Initializing LLM-based correction system...")
        self.translator = Aya23Translator(model_path)
        print("[OK] Ready for LLM corrections\n")

    def extract_tags(self, text: str) -> Tuple[str, List[Tuple[int, str]]]:
        """Extract Ren'Py tags/variables, return clean text and tag positions"""
        tags = []
        clean_text = text

        # Find all tags and variables
        all_matches = []
        for match in self.TAG_PATTERN.finditer(text):
            all_matches.append((match.start(), match.group()))
        for match in self.VAR_PATTERN.finditer(text):
            all_matches.append((match.start(), match.group()))

        # Sort by position (reverse order for removal)
        all_matches.sort(key=lambda x: x[0], reverse=True)

        # Remove tags from text and store positions
        for pos, tag in all_matches:
            before_tag = text[:pos]
            tags.insert(0, (len(before_tag), tag))
            clean_text = clean_text[:pos] + clean_text[pos + len(tag):]

        return clean_text.strip(), tags

    def restore_tags(self, corrected_text: str, tags: List[Tuple[int, str]], original_text: str) -> str:
        """Restore tags into corrected text based on relative positions"""
        if not tags:
            return corrected_text

        result = corrected_text
        original_len = len(original_text)
        corrected_len = len(corrected_text)

        sorted_tags = sorted(tags, key=lambda x: x[0], reverse=True)

        for orig_pos, tag in sorted_tags:
            if original_len > 0:
                ratio = orig_pos / original_len
                new_pos = int(ratio * corrected_len)
            else:
                new_pos = 0

            new_pos = max(0, min(new_pos, len(result)))

            # CRITICAL FIX: Ensure we don't insert inside another tag
            safe_pos = self._find_safe_insertion_point(result, new_pos)

            result = result[:safe_pos] + tag + result[safe_pos:]

        return result

    @staticmethod
    def _find_safe_insertion_point(text: str, target_pos: int) -> int:
        """
        Find a safe position to insert a tag, ensuring we don't break existing tags

        Args:
            text: The text to insert into
            target_pos: The desired insertion position

        Returns:
            A safe position that won't break existing tags
        """
        # Clamp to text bounds
        target_pos = max(0, min(target_pos, len(text)))

        # Check if we're inside a tag at target_pos
        # Count unclosed braces/brackets before this position
        before_text = text[:target_pos]

        # Count { and } before target
        open_braces = before_text.count('{')
        close_braces = before_text.count('}')

        # Count [ and ] before target
        open_brackets = before_text.count('[')
        close_brackets = before_text.count(']')

        # If we're inside a tag, find the end of it
        if open_braces > close_braces:
            # We're inside {}, find the next }
            next_close = text.find('}', target_pos)
            if next_close != -1:
                return next_close + 1

        if open_brackets > close_brackets:
            # We're inside [], find the next ]
            next_close = text.find(']', target_pos)
            if next_close != -1:
                return next_close + 1

        # Position is safe
        return target_pos

    def create_correction_prompt(self, romanian_text: str) -> str:
        """Create prompt for correcting Romanian text"""
        prompt = f"""You are a Romanian grammar expert. Correct ONLY the grammatical errors in this Romanian text.

CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
1. Fix verb conjugations (especially subjunctive mood with "să")
   Example: "să merge" → "să meargă" or "să vadă" instead of "să vede"
2. Fix reflexive pronouns (te, se, mă, ne, vă) when grammatically required
   Example: "Vreau să spăl" → "Vreau să mă spăl" (reflexive: to wash oneself)
3. Fix gender/number agreement (adjectives must match nouns)
4. Fix diacritics (adica → adică, etc.)
5. Fix spelling errors (nici una → niciuna)

ABSOLUTE PROHIBITIONS - NEVER DO THESE:
1. NEVER change proper names (names of people, places) - keep capitalized words EXACTLY as-is
2. NEVER change punctuation (keep ..., ?!?, !!, etc. exactly as written)
3. NEVER remove or add words unless fixing grammar (keep meaning 100% identical)
4. NEVER change sentence structure unless grammatically wrong
5. NEVER add or remove spaces around ... or other punctuation
6. If text is already grammatically correct, return it UNCHANGED
7. Do NOT translate to English
8. Do NOT add explanations

Romanian text to correct: {romanian_text}
Corrected Romanian:"""
        return prompt

    def correct_text(self, romanian_text: str) -> Tuple[str, bool]:
        """
        Correct Romanian grammar/conjugation errors using LLM

        Returns:
            (corrected_text, was_changed)
        """
        # Safety check: Skip malformed tags
        if re.search(r'\{[^}]*\{', romanian_text) or re.search(r'\}[^{]*\}(?![^{]*$)', romanian_text):
            return romanian_text, False

        # Extract tags first
        clean_text, tags = self.extract_tags(romanian_text)

        if not clean_text.strip():
            return romanian_text, False

        # Create correction prompt
        prompt = self.create_correction_prompt(clean_text)

        # Get correction from model
        output = self.translator.llm(
            prompt,
            max_tokens=512,
            temperature=0.2,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["English:", "\n\n", "Romanian text to correct:", "Corrected Romanian:"],
            echo=False
        )

        corrected = output['choices'][0]['text'].strip()

        # Clean up artifacts
        corrected = self._clean_output(corrected)

        # Restore tags
        final_text = self.restore_tags(corrected, tags, clean_text)

        # Verify tag restoration
        original_tag_count = len(re.findall(r'\{[^}]+\}|\[[^\]]+\]', romanian_text))
        corrected_tag_count = len(re.findall(r'\{[^}]+\}|\[[^\]]+\]', final_text))
        if original_tag_count != corrected_tag_count:
            return romanian_text, False

        # Validate correction
        if not self._validate_correction(romanian_text, final_text):
            return romanian_text, False

        # Fix spacing around variables
        final_text = re.sub(r'(\S)(\[[\w\s]+\])', r'\1 \2', final_text)
        final_text = re.sub(r'(\[[\w\s]+\])([a-zA-Z]+)',
                           lambda m: m.group(1) + (' ' + m.group(2) if m.group(2) not in ['u', 'a', 'i'] else ''),
                           final_text)

        was_changed = (final_text != romanian_text)
        return final_text, was_changed

    def _validate_correction(self, original: str, corrected: str) -> bool:
        """Validate that correction doesn't violate rules"""
        # Don't allow proper name changes
        original_caps = set(re.findall(r'\b[A-Z][a-z]+', original))
        corrected_caps = set(re.findall(r'\b[A-Z][a-z]+', corrected))
        if original_caps != corrected_caps:
            return False

        # Don't allow punctuation changes
        orig_punct = re.findall(r'[.!?,;:\-—…]', original)
        corr_punct = re.findall(r'[.!?,;:\-—…]', corrected)
        if orig_punct != corr_punct:
            return False

        # Don't allow quote style changes
        if original.count("'") != corrected.count("'"):
            return False
        if original.count('"') != corrected.count('"'):
            return False

        # Word count shouldn't change drastically
        orig_words = len(original.split())
        corr_words = len(corrected.split())
        if abs(orig_words - corr_words) > 2:
            return False

        # Spacing around variables
        if ' [' in original and ' [' not in corrected:
            return False

        # Text length shouldn't change drastically
        if len(corrected) > len(original) * 1.3 or len(corrected) < len(original) * 0.7:
            return False

        return True

    def _clean_output(self, text: str) -> str:
        """Clean up model output artifacts"""
        for prefix in ["Corrected Romanian:", "Romanian:", "Translation:", "Corected:"]:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()

        lines = text.split('\n')
        if lines:
            text = lines[0].strip()

        text = text.strip('"').strip("'")
        return text


class CombinedCorrector:
    """Combines pattern-based and LLM-based corrections"""

    def __init__(self,
                 patterns_corrector: Optional[PatternBasedCorrector] = None,
                 llm_corrector: Optional[LLMBasedCorrector] = None):
        """
        Initialize combined corrector

        Args:
            patterns_corrector: Pattern-based corrector (or None to skip)
            llm_corrector: LLM-based corrector (or None to skip)
        """
        self.patterns = patterns_corrector
        self.llm = llm_corrector

    @staticmethod
    def sanitize_quotes(text: str) -> Tuple[str, bool]:
        """
        Sanitize quotes in text to prevent Ren'Py syntax errors.

        CRITICAL: Ren'Py uses Python syntax, so strings delimited by " cannot contain unescaped "
        This function converts nested quotes to '' (two single quotes) format.

        Args:
            text: Translation text that may contain quote issues

        Returns:
            (sanitized_text, was_changed)
        """
        original_text = text

        # Replace any nested double quotes with two single quotes
        # This is safe because we're already inside a double-quoted string
        sanitized = text.replace('"', "''")

        # Also fix escaped quotes (\" or \") that slipped through
        sanitized = sanitized.replace('\\"', "''").replace('\\"', "''")

        # Fix single escaped single quotes
        sanitized = sanitized.replace("\\'", "'")

        was_changed = (sanitized != original_text)
        return sanitized, was_changed

    def correct_text(self, text: str) -> Tuple[str, Dict]:
        """
        Apply corrections in order: quote sanitization, patterns, then LLM

        Returns:
            (corrected_text, changes_dict)
        """
        corrected = text
        changes = {
            'quote_sanitized': False,
            'pattern_changes': [],
            'llm_changed': False,
            'pattern_corrected': text,
            'llm_corrected': text
        }

        # Step 0: Quote sanitization (CRITICAL - prevents syntax errors)
        corrected, quote_changed = self.sanitize_quotes(corrected)
        changes['quote_sanitized'] = quote_changed

        # Step 1: Pattern-based corrections (fast)
        if self.patterns:
            corrected, pattern_changes = self.patterns.correct_text(corrected)
            changes['pattern_changes'] = pattern_changes
            changes['pattern_corrected'] = corrected

        # Step 2: LLM-based corrections (slow)
        if self.llm:
            corrected, llm_changed = self.llm.correct_text(corrected)
            changes['llm_changed'] = llm_changed
            changes['llm_corrected'] = corrected

        return corrected, changes


class RenpyFileCorrector:
    """Parse and correct Ren'Py translation files"""

    # Updated patterns to handle strings with unescaped quotes
    # Match everything up to the end of line instead of stopping at quotes
    TRANSLATE_BLOCK_PATTERN = re.compile(
        r'(# game/[^\n]+\n'
        r'translate \w+ \w+:\s*\n'
        r'\s*# [^\n]+\n'
        r'\s*\w+ ")(.+?)("(?:[ \t]*#.*)?)[ \t]*$',
        re.MULTILINE
    )

    STRING_BLOCK_PATTERN = re.compile(
        r'(# game/[^\n]+\n'
        r'\s*old "[^\n]*?"\s*\n'
        r'\s*new ")(.+?)("(?:[ \t]*#.*)?)[ \t]*$',
        re.MULTILINE
    )

    def __init__(self, corrector: CombinedCorrector, dry_run: bool = False):
        self.corrector = corrector
        self.dry_run = dry_run

    def correct_file(self, file_path: Path) -> Dict:
        """Correct all Romanian translations in a single .rpy file"""
        print(f"\nProcessing: {file_path.name}")

        content = file_path.read_text(encoding='utf-8')
        original_content = content

        all_changes = []
        blocks_processed = 0
        start_time = time.time()

        # Count total blocks for progress
        total_count = len(self.TRANSLATE_BLOCK_PATTERN.findall(content)) + \
                     len(self.STRING_BLOCK_PATTERN.findall(content))

        def correct_match(match, block_type):
            nonlocal blocks_processed
            blocks_processed += 1

            prefix = match.group(1)
            old_translation = match.group(2)
            suffix = match.group(3)

            if not old_translation.strip():
                return match.group(0)

            # Extract English source text from comment
            english_source = ""
            if block_type == 'dialogue':
                # For dialogue blocks: extract from "# character "English text""
                # Handle nested quotes by capturing everything between the first " and last "
                comment_match = re.search(r'#\s+\w+\s+"(.+)"', prefix)
                if comment_match:
                    english_source = comment_match.group(1)
            elif block_type == 'string':
                # For string blocks: extract from 'old "English text"'
                # Handle nested quotes by capturing everything between the first " and last "
                old_match = re.search(r'old\s+"(.+?)"', prefix)
                if old_match:
                    english_source = old_match.group(1)

            # Show progress
            show_progress(blocks_processed, total_count, start_time, prefix="  ")

            new_translation, change_info = self.corrector.correct_text(old_translation)

            if new_translation != old_translation:
                change_record = {
                    'block_type': block_type,
                    'block_number': blocks_processed,
                    'english_source': english_source,
                    'old': old_translation,
                    'new': new_translation,
                    'quote_sanitized': change_info.get('quote_sanitized', False),
                    'pattern_changes': change_info.get('pattern_changes', []),
                    'llm_changed': change_info.get('llm_changed', False)
                }
                all_changes.append(change_record)

            return prefix + new_translation + suffix

        # Apply corrections
        content = self.TRANSLATE_BLOCK_PATTERN.sub(lambda m: correct_match(m, 'dialogue'), content)
        content = self.STRING_BLOCK_PATTERN.sub(lambda m: correct_match(m, 'string'), content)

        # Clear progress line and show completion
        print()  # Newline after progress bar
        print(f"  Processed {blocks_processed} blocks, made {len(all_changes)} corrections")

        # Show corrections summary
        if all_changes:
            quote_count = sum(1 for c in all_changes if c['quote_sanitized'])
            pattern_count = sum(1 for c in all_changes if c['pattern_changes'])
            llm_count = sum(1 for c in all_changes if c['llm_changed'])

            print(f"\n  Corrections made:")
            print(f"    Quote sanitization: {quote_count}")
            print(f"    Pattern-based: {pattern_count}")
            print(f"    LLM-based: {llm_count}")

            for i, change in enumerate(all_changes[:5], 1):
                english = change.get('english_source', '')
                display_text = english[:60] if english else f"[{change['block_type']}]"
                print(f"\n    {i}. {display_text}")
                if change['quote_sanitized']:
                    print(f"       [QUOTE] Fixed unescaped quotes")
                if change['pattern_changes']:
                    for pc in change['pattern_changes']:
                        print(f"       [PATTERN:{pc['type']}] {pc['old']} → {pc['new']}")
                if change['llm_changed']:
                    print(f"       [LLM] Grammar correction applied")
                print(f"       OLD: {change['old'][:70]}")
                print(f"       NEW: {change['new'][:70]}")

            if len(all_changes) > 5:
                print(f"\n    ... and {len(all_changes) - 5} more")

            # Save corrections to file
            corrections_file = file_path.with_suffix('.corrections.txt')
            with open(corrections_file, 'w', encoding='utf-8') as f:
                f.write(f"Corrections for: {file_path.name}\n")
                f.write(f"Total corrections: {len(all_changes)}\n")
                f.write(f"  Quote sanitization: {quote_count}\n")
                f.write(f"  Pattern-based: {pattern_count}\n")
                f.write(f"  LLM-based: {llm_count}\n")
                f.write("=" * 80 + "\n\n")

                for i, change in enumerate(all_changes, 1):
                    english_source = change.get('english_source', '')
                    if english_source:
                        f.write(f"{i}. ENGLISH: {english_source}\n")
                    else:
                        f.write(f"{i}. [{change['block_type'].upper()}]\n")

                    if change['quote_sanitized']:
                        f.write(f"   [QUOTE] Fixed unescaped quotes\n")
                    if change['pattern_changes']:
                        for pc in change['pattern_changes']:
                            f.write(f"   [PATTERN:{pc['type']}] {pc['old']} → {pc['new']}\n")
                    if change['llm_changed']:
                        f.write(f"   [LLM] Grammar correction applied\n")
                    f.write(f"   OLD: {change['old']}\n")
                    f.write(f"   NEW: {change['new']}\n")
                    f.write("-" * 80 + "\n")

            print(f"  [SAVED] Full corrections list: {corrections_file}")

        # Write or preview
        if self.dry_run:
            print(f"  [DRY RUN] Would write {len(all_changes)} corrections")
        elif all_changes:
            file_path.write_text(content, encoding='utf-8')
            print(f"  [OK] Written {len(all_changes)} corrections")
        else:
            print(f"  [OK] No corrections needed")

        return {
            'total_blocks': blocks_processed,
            'corrections': len(all_changes),
            'changed': content != original_content
        }

    def correct_directory(self, directory: Path) -> Dict:
        """Correct all .rpy files in a directory"""
        rpy_files = list(directory.rglob("*.rpy"))

        if not rpy_files:
            print(f"No .rpy files found in {directory}")
            return {'files': 0, 'total_blocks': 0, 'total_corrections': 0}

        print(f"\nFound {len(rpy_files)} files to correct")
        print("=" * 70)

        total_stats = {
            'files': 0,
            'files_changed': 0,
            'total_blocks': 0,
            'total_corrections': 0
        }

        # Process files with progress tracking
        dir_start_time = time.time()

        for file_idx, rpy_file in enumerate(rpy_files):
            # Show overall progress for multi-file correction
            if len(rpy_files) > 1:
                print()
                show_progress(file_idx, len(rpy_files), dir_start_time, prefix="Overall: ")
                print(f"\n[File {file_idx + 1}/{len(rpy_files)}]", flush=True)

            stats = self.correct_file(rpy_file)

            total_stats['files'] += 1
            total_stats['total_blocks'] += stats['total_blocks']
            total_stats['total_corrections'] += stats['corrections']
            if stats['changed']:
                total_stats['files_changed'] += 1

        print("\n" + "=" * 70)
        print("CORRECTION COMPLETE")
        print(f"  Files processed: {total_stats['files']}")
        print(f"  Files changed: {total_stats['files_changed']}")
        print(f"  Blocks reviewed: {total_stats['total_blocks']}")
        print(f"  Corrections made: {total_stats['total_corrections']}")

        if self.dry_run:
            print("\n  [DRY RUN] No files were modified")

        return total_stats


def detect_language_from_path(path: Path) -> str:
    """
    Auto-detect target language from path (e.g., "game/tl/romanian" → "Romanian")

    Returns capitalized language name (e.g., "Romanian", "Spanish", "French")
    """
    path_str = str(path).lower().replace('\\', '/')

    # Language mappings (path name → proper name)
    lang_map = {
        'romanian': 'Romanian',
        'spanish': 'Spanish',
        'french': 'French',
        'german': 'German',
        'italian': 'Italian',
        'portuguese': 'Portuguese',
        'russian': 'Russian',
        'turkish': 'Turkish',
        'czech': 'Czech',
        'polish': 'Polish',
        'ukrainian': 'Ukrainian'
    }

    for path_name, proper_name in lang_map.items():
        if path_name in path_str:
            return proper_name

    return "Romanian"  # Default fallback


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    dry_run = '--dry-run' in sys.argv
    patterns_only = '--patterns-only' in sys.argv
    llm_only = '--llm-only' in sys.argv

    if not input_path.exists():
        print(f"Error: Path not found: {input_path}")
        sys.exit(1)

    # Validate options
    if patterns_only and llm_only:
        print("Error: Cannot use both --patterns-only and --llm-only")
        sys.exit(1)

    # Detect language from path
    target_language = detect_language_from_path(input_path)

    # Map language names to ISO codes
    lang_code_map = {
        'Romanian': 'ro',
        'Spanish': 'es',
        'French': 'fr',
        'German': 'de',
        'Italian': 'it',
        'Portuguese': 'pt',
        'Russian': 'ru',
        'Turkish': 'tr',
        'Czech': 'cs',
        'Polish': 'pl',
        'Ukrainian': 'uk'
    }
    lang_code = lang_code_map.get(target_language, target_language.lower()[:2])

    # Setup paths
    project_root = Path(__file__).parent.parent

    # Load configuration from current_config.json
    config_file = project_root / "models" / "current_config.json"
    if not config_file.exists():
        print(f"ERROR: Configuration not found at {config_file}")
        print("Please run 1-config.ps1 first to set up your game.")
        sys.exit(1)

    with open(config_file, 'r', encoding='utf-8-sig') as f:
        full_config = json.load(f)
    game_config = full_config['games'][full_config['current_game']] # Load specific game config

    model_name = game_config['model']

    # Load model configuration from models_config.json
    models_config_path = project_root / "models" / "models_config.json"
    with open(models_config_path, 'r', encoding='utf-8-sig') as f:
        all_models_config = json.load(f)['available_models']

    model_config = all_models_config.get(model_name)

    if not model_config:
        print(f"ERROR: Model '{model_name}' not found in models_config.json")
        sys.exit(1)

    model_path = project_root / model_config['destination']

    # Generic corrections fallback: uncensored → censored → none
    corrections_file = None
    for corrections_variant in [f"{lang_code}_uncensored_corrections.json", f"{lang_code}_corrections.json"]:
        candidate = project_root / "data" / corrections_variant
        if candidate.exists():
            corrections_file = candidate
            print(f"[OK] Using corrections: {corrections_variant}")
            break

    # Initialize correctors based on flags
    patterns_corrector = None
    llm_corrector = None

    if not llm_only:
        if not corrections_file:
            print(f"[WARNING] No corrections file found for {target_language} ({lang_code})")
            if patterns_only:
                print("Error: --patterns-only requires a corrections file")
                sys.exit(1)
            print("[INFO] Skipping pattern-based corrections")
        else:
            patterns_corrector = PatternBasedCorrector(str(corrections_file))

    if not patterns_only:
        if not model_path.exists():
            print(f"Error: Model not found at {model_path}")
            sys.exit(1)
        llm_corrector = LLMBasedCorrector(str(model_path))

    # Create combined corrector
    combined = CombinedCorrector(patterns_corrector, llm_corrector)
    file_corrector = RenpyFileCorrector(combined, dry_run=dry_run)

    # Show mode
    mode = []
    if patterns_corrector:
        mode.append("Pattern-based")
    if llm_corrector:
        mode.append("LLM-based")
    print(f"\nCorrection mode: {' + '.join(mode)}")
    print("=" * 70)

    # Correct files
    if input_path.is_file():
        file_corrector.correct_file(input_path)
    else:
        file_corrector.correct_directory(input_path)


if __name__ == "__main__":
    main()
